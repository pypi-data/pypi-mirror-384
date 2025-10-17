import polars as pl
from pathlib import Path
from typing import Union, Dict, Literal, List, Optional

def table_relpath(filenames: Union[pl.Expr, pl.Series], start: str) -> Union[pl.Expr, pl.Series]:
    if not start.endswith('/'):
        start = start + '/'
    
    return filenames.str.replace(f'^{start}', '')

def table_file_ext(filenames: Union[pl.Expr, pl.Series]) -> Union[pl.Expr, pl.Series]:
    return filenames.str.extract('(\.[^\.]+$)')

def table_path_basename(filenames: Union[pl.Expr, pl.Series]) -> Union[pl.Expr, pl.Series]:
    return filenames.str.extract('/?([^/]+)$')

def table_join_paths(left: Union[pl.Expr, pl.Series, str, Path],
                     right: Union[pl.Expr, pl.Series, str, Path]) -> Union[pl.Expr, pl.Series]:
    if isinstance(left, (str, Path)):
        assert isinstance(right, (pl.Series, pl.Expr)), f'left or right must be pl.Series or pl.Expr, \
            got left: {type(left)}, right: {type(right)}'
        left = pl.lit(str(left))
        is_series = isinstance(right, pl.Series)
    else:
        is_series = isinstance(left, pl.Series)
        assert isinstance(right, (str, Path, type(left))), f'cannot join {type(left)} on left with {type(right)} on right'
    
    if isinstance(right, (str, Path)):
        right = pl.lit(str(right))
        
    expr = pl.when(right.str.starts_with('/')).then(
        right
    ).otherwise(
        pl.when(left.str.ends_with('/')).then(
            left + right
        ).otherwise(
            left + '/' + right
        )
    )

    if is_series:
        return pl.select(expr).to_series()

    return expr

def align_table_schema(df: Union[pl.DataFrame, pl.LazyFrame], schema: Dict[str, pl.DataType]) -> pl.DataFrame:
    curr_schema = df.schema
    exprs = []

    for column, dtype in schema.items():
        if column not in curr_schema:
            exprs.append(pl.lit(None, dtype=dtype).alias(column))
        elif curr_schema[column] != dtype:
            exprs.append(pl.col(column).cast(dtype))

    if len(exprs) > 0:
        df = df.with_columns(exprs)

    return df.select(schema.keys())

def align_schemas(schemas: List[Dict[str, pl.DataType]],
                  on_conflict: Literal['left', 'right', 'drop', 'error'] = 'error'
                  ) -> Dict[str, pl.DataType]:
    assert len(schemas) > 0, 'no schemas were provided'

    aligned_schema = schemas[0].copy()

    for schema in schemas[1:]:
        common_cols = set(aligned_schema).intersection(set(schema))
        conflicting_cols = [col for col in common_cols if aligned_schema[col] != schema[col]]

        if len(conflicting_cols) > 0:
            if on_conflict == 'error':
                conflict1 = [aligned_schema[col] for col in conflicting_cols]
                conflict2 = [schema[col] for col in conflicting_cols]
                raise TypeError(f'conflicting schema, on left: {conflict1}, on right: {conflict2}')
            elif on_conflict == 'left':
                tmp_schema = schema.copy()
                tmp_schema.update(aligned_schema)
                aligned_schema = tmp_schema
            elif on_conflict == 'right':
                aligned_schema.update(schema)
            elif on_conflict == 'drop':
                aligned_schema.update(schema)

                for col in conflicting_cols:
                    aligned_schema.pop(col)
            else:
                raise ValueError(f'unknown value "{on_conflict}" for on_conflict argument')
        else:
            aligned_schema.update(schema)
    
    return aligned_schema

def align_and_concat(dataframes: List[Union[pl.DataFrame, pl.LazyFrame, str, Path]],
                     on_conflict: Literal['left', 'right', 'drop', 'error'] = 'error',
                     on_file_not_exists: Literal['ignore', 'error'] = 'error',
                     on_loading_error: Literal['ignore', 'error'] = 'error',
                     eager: bool = False) -> Union[pl.DataFrame, pl.LazyFrame, None]:
    if len(dataframes) == 0:
        return None
    
    df_list = []

    for df in dataframes:
        if isinstance(df, (str, Path)):
            df_path = Path(df)

            if df_path.exists():
                try:
                    df = pl.scan_parquet(df_path)
                except Exception as e:
                    if on_loading_error == 'error':
                        raise e
                    continue
            else:
                if on_file_not_exists == 'error':
                    raise FileNotFoundError(f'unable to find file in {df_path}')
                continue
        elif isinstance(df, pl.DataFrame):
            df = df.lazy()
        elif not isinstance(df, pl.LazyFrame):
            raise TypeError(f'unsupported type {type(df)}')
        
        df_list.append(df)

    if len(df_list) == 0:
        return None

    aligned_schema = align_schemas([df.schema for df in df_list], on_conflict=on_conflict)
    concat_df = pl.concat([align_table_schema(df, aligned_schema) for df in df_list])

    return concat_df.collect() if eager else concat_df


def table_path_join(df: Union[pl.DataFrame, pl.LazyFrame], column: str, start: Union[str, Path] = None,
                    end: Union[str, Path] = None) -> Union[pl.DataFrame, pl.LazyFrame]:
    if start is not None:
        start = str(start)
        if start.endswith('/'):
            start = start[:-1]

        df = df.with_columns(
            pl.when(pl.col(column).str.starts_with('/')).then(
                pl.col(column)
            ).otherwise(
                start + '/' + pl.col(column)
            ).alias(column)
        )
    
    if end is not None:
        end = str(end)
        if end.startswith('/'):
            end = end[1:]

        df = df.with_columns(
            pl.when(pl.col(column).str.ends_with('/')).then(
                pl.col(column) + end
            ).otherwise(
                pl.col(column) + '/' + end
            ).alias(column)
        )
        
    return df

def relaxed_concat(table_list: List[Union[pl.DataFrame, pl.LazyFrame]]
                   ) -> Optional[Union[pl.DataFrame, pl.LazyFrame]]:
    valid_tables = [table for table in table_list if table is not None]

    if len(valid_tables) > 0:
        return pl.concat(valid_tables)

    return None

def contains_columns(df: Union[pl.DataFrame, pl.LazyFrame, str, Path], column: Union[str, List[str]],
                     on_file_not_exists: Literal['ignore', 'error'] = 'ignore') -> bool:
    if isinstance(column, str):
        column = [column]
    
    if isinstance(df, (pl.DataFrame, pl.LazyFrame)):
        existing_columns = set(df.columns)
        return all([col in existing_columns for col in column])
    
    df_path = Path(df)

    if df_path.exists():
        existing_columns = pl.read_parquet_schema(df_path)
        return all([col in existing_columns for col in column])

    if on_file_not_exists == 'error':
        raise FileNotFoundError(f'cannot find file {df_path}')

    return False