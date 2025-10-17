from uuid import UUID


from fastdup.vl.common.logging_init import get_vl_logger
from fastdup.vldbaccess import sql_template_utils
from fastdup.vldbaccess.connection_manager import get_async_session, get_engine_dialect
import sqlalchemy as sa
from fastdup.vl.common.settings import Settings

from fastdup.vldbaccess.sql_template_utils import QueryModule

if not Settings.IS_FASTDUP:
    from psycopg.errors import QueryCanceled, InFailedSqlTransaction


logger = get_vl_logger(__name__)

QUERY_CONDITION_WORDS = {"and", "or", "-", "+", "&", "|"}

STOP_WORDS = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours',
'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself',
'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself',
'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are',
 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for',
'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to',
'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y',
 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't",
'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn',
 "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"}


INITIAL_RESULT_SET_SIZE = 50
FINAL_RESULT_SET_SIZE = 10
MAX_WORDS_IN_RESPONSE = 5


async def _get_autocomplete_suggestions(
        dataset_id: UUID, query: str, query_limit=INITIAL_RESULT_SET_SIZE) -> list[tuple[str, list[str]]]:
    sql_query = sql_template_utils.render(
        QueryModule.EXPLORATION, "autocomplete.jinja2", limit=query_limit
    )

    formatted_query = " & ".join(query.split(" ")) + ":*"
    ctx = {"dataset_id": dataset_id, "query": formatted_query}
    async with get_async_session() as session:
        if get_engine_dialect() == "postgresql":
            try:
                await session.begin()
                await session.execute(sa.text("SET statement_timeout=1000;"))  # set timeout
                query_result = await session.execute(sa.text(sql_query), ctx)
                rows = query_result.all()
            except (QueryCanceled, InFailedSqlTransaction) as e:
                logger.warning("autosuggest query canceled due to timeout",
                               extra=ctx)
                await session.rollback()
                rows = []
            except Exception as e:
                await session.rollback()
                logger.error("autosuggest query", exc_info=True)
                rows = []
            finally:
                await session.execute(sa.text("SET statement_timeout=0;"))  # disable timeout, probably unneeded
        else:
            query_result = await session.execute(
                sa.text(sql_query), ctx)
            rows = query_result.all()

    return rows


async def get_autocomplete_suggestions(
        dataset_id: UUID, query: str, limit=FINAL_RESULT_SET_SIZE, query_limit=INITIAL_RESULT_SET_SIZE) -> list[str]:
    """
    - auto suggest results will contain up to 5 words, suggestions with more words will be dropped
    - no handling of condition (AND OR) words no autocomplete suggestion would be given
    - results would be sorted according to word count
    """
    query = query.lower().strip()
    if set(query.split(" ")).intersection(QUERY_CONDITION_WORDS):  # do not handle queries that contains conditions
        return []
    rows = await _get_autocomplete_suggestions(dataset_id, query, query_limit)
    modified_suggestions = modify_suggestions(query, rows, limit)

    suggestions = [(suggestion, len(suggestion.split(" "))) for suggestion in modified_suggestions]
    filtered_suggestions = filter(lambda x: x[1] <= MAX_WORDS_IN_RESPONSE, suggestions)
    sorted_suggestions = sorted(filtered_suggestions, key=lambda x: x[1])
    return [w[0] for w in sorted_suggestions]


def modify_suggestions(query, suggestions: list[tuple[str, list[str]]], limit=FINAL_RESULT_SET_SIZE) -> list[str]:
    modified_suggestions: set[str] = set()
    for caption, labels in suggestions:
        if len(modified_suggestions) > limit:
            break
        modified_suggestion = _modify_suggestion(query, caption, labels)
        if modified_suggestion:
            modified_suggestions.add(modified_suggestion)

    return list(modified_suggestions)  # deduplicate


def _iter_suggestion(suggestion_list: list[str], query_end_idx: int):
    for idx, word in enumerate(suggestion_list):
        if idx <= query_end_idx:
            yield word
        elif word in STOP_WORDS:
            yield word
        else:
            yield word
            break


def _modify_suggestion(query, caption: str, labels: list[str]) -> str:
    caption_list = caption.split(" ")
    query_list = query.split(" ")
    query_end_idx = max(
        (idx for idx, word in enumerate(caption_list) if word in query_list and word not in STOP_WORDS),
        default=None)
    if query_end_idx is not None:  # query is part of the caption
        return " ".join(_iter_suggestion(caption_list, query_end_idx))

    last_query_word = query_list[-1]

    last_query_word_idx = caption.find(last_query_word)
    if last_query_word_idx >= 0:  # return caption, up until the end of the partial query word
        break_after_query_word = caption[last_query_word_idx:].find(" ")
        if break_after_query_word == -1:
            return caption
        return caption[:last_query_word_idx + break_after_query_word]

    else:  # query word cannot be found in caption (even as a partial word)
        label_match = sorted(
            [word for word in labels if word.find(last_query_word) != -1],
            key=lambda word: len(word), reverse=True
        )
        if label_match:
            return label_match[0]
    logger.debug("failed to process auto-suggest input",
                 extra={"query": query, "caption": caption, "labels": labels})
    return caption  # no modification rule applied
