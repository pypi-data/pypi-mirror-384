SET TimeZone='UTC';

DROP TABLE IF EXISTS users_to_groups CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS datasets CASCADE;
DROP TABLE IF EXISTS clusters CASCADE;
DROP TABLE IF EXISTS images CASCADE;
DROP TABLE IF EXISTS images_to_clusters CASCADE;
DROP TABLE IF EXISTS access CASCADE;
DROP TABLE IF EXISTS labels CASCADE;
DROP TABLE IF EXISTS label_categories CASCADE;
DROP TABLE IF EXISTS dataset_issues CASCADE;
DROP TABLE IF EXISTS image_issues CASCADE;
DROP TABLE IF EXISTS issue_type CASCADE;
DROP TABLE IF EXISTS objects CASCADE;
DROP TABLE IF EXISTS objects_to_images CASCADE;
DROP TABLE IF EXISTS similarity_clusters CASCADE;
DROP TABLE IF EXISTS images_to_similarity_clusters CASCADE;
DROP TABLE IF EXISTS objects_to_similarity_clusters CASCADE;
DROP TABLE IF EXISTS image_similarity_mapping CASCADE;
DROP TABLE IF EXISTS object_similarity_mapping CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS media_to_tags CASCADE;
DROP TABLE IF EXISTS media_to_captions CASCADE;
DROP TABLE IF EXISTS flow_runs CASCADE;
DROP TABLE IF EXISTS flat_similarity_clusters CASCADE;
DROP TABLE IF EXISTS image_vector CASCADE;
DROP TABLE IF EXISTS query_vector_embedding CASCADE;
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS export_task CASCADE;
DROP TABLE IF EXISTS user_groups CASCADE;

DROP SEQUENCE IF EXISTS seq_flow_runs_id;

DROP TYPE IF EXISTS dataset_source_type CASCADE;
DROP TYPE IF EXISTS dataset_status CASCADE;
DROP TYPE IF EXISTS dataset_sample CASCADE;
DROP TYPE IF EXISTS cluster_type CASCADE;
DROP TYPE IF EXISTS access_operation CASCADE;
DROP TYPE IF EXISTS name_value CASCADE;
DROP TYPE IF EXISTS label_type CASCADE;
DROP TYPE IF EXISTS similarity_threshold CASCADE;
DROP TYPE IF EXISTS similarity_cluster_type CASCADE;
DROP TYPE IF EXISTS clustering_method CASCADE;
DROP TYPE IF EXISTS metadata_source CASCADE;
DROP TYPE IF EXISTS export_task_status CASCADE;

-- Create Types before Tables
CREATE TYPE similarity_threshold AS ENUM ('0', '1', '2', '3', '4');
CREATE TYPE similarity_cluster_type AS ENUM ('IMAGES', 'OBJECTS');
CREATE TYPE clustering_method AS ENUM ('SIMILARITY', 'LABEL', 'VIDEO');
CREATE TYPE metadata_source AS ENUM ('VL', 'USER');
CREATE TYPE dataset_source_type AS ENUM ('VL', 'PUBLIC_BUCKET', 'UPLOAD');
CREATE TYPE dataset_status AS ENUM ('UPLOADING', 'SAVING', 'INDEXING', 'READY', 'FATAL_ERROR');
CREATE TYPE dataset_sample AS ENUM ('SAMPLE', 'DEFAULT_SAMPLE');

CREATE TABLE users
(
    id                uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    user_identity     text NOT NULL,
    identity_provider text NOT NULL, -- google, github, etc.
    email             text,
    name              text,
    avatar_uri        text,
    created_at        timestamp DEFAULT now(),
    dataset_quota     int       DEFAULT 10,
    assume_role       text
--     org_id            uuid,
);
CREATE UNIQUE INDEX user_identity_idx ON users (user_identity, identity_provider);

CREATE TABLE api_keys
(
    api_key              uuid NOT NULL,
    encrypted_api_secret text NOT NULL,
    user_id              uuid NOT NULL UNIQUE,
    created_at           timestamp DEFAULT now()
);


CREATE TABLE datasets
(
    id                 uuid                DEFAULT gen_random_uuid() PRIMARY KEY,
    created_by         uuid                NOT NULL,
    owned_by           text                NOT NULL,
    display_name       text                NOT NULL,
    description        text,
    preview_uri        text,
    source_type        dataset_source_type NOT NULL,
    source_uri         text,
    created_at         timestamp                    DEFAULT now(),
    filename           text,
    sample             dataset_sample,
    status             dataset_status      NOT NULL DEFAULT 'UPLOADING',
    fatal_error_msg    text,
    progress           int                 NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    score              int                 NOT NULL DEFAULT 0,
    stats              json                 DEFAULT array [],
    n_images           int                          DEFAULT -1,
    n_objects          int                          DEFAULT -1,
    n_clusters         int                          DEFAULT -1,
    n_videos           int                          DEFAULT -1,
    n_video_frames     int                          DEFAULT -1,
    size_bytes         bigint                       DEFAULT -1,
    deleted            boolean             NOT NULL DEFAULT false,
    thumbnails         boolean             NOT NULL DEFAULT false,
    pipeline_commit_id text,
    thresholds         json                 DEFAULT NULL,
    media_embeddings   boolean             NOT NULL DEFAULT false,
    media_embeddings_cosine_distance   boolean             NOT NULL DEFAULT false
);


CREATE TABLE issue_type
(
    id       int PRIMARY KEY,
    name     text UNIQUE,
    severity int -- lower is higher
);

CREATE TYPE cluster_type AS ENUM ('CLUSTERS', 'IMAGES', 'OBJECTS');
CREATE TABLE clusters
(
    id               uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    dataset_id       uuid         NOT NULL,
    display_name     text,
    parent_id        uuid,
    type             cluster_type NOT NULL,
    issue_type_id    int,
    preview_uri      text         NOT NULL,
    n_images         int,
    n_clusters       int,
    n_child_clusters int,
    n_objects        int,
    n_videos         int,
    n_video_frames   int,
    size_bytes       bigint
);
CREATE INDEX clusters_parent_id ON clusters (parent_id);

CREATE TABLE similarity_clusters
(
    id                   uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    dataset_id           uuid                    NOT NULL,
    display_name         text,
    similarity_threshold similarity_threshold    NOT NULL,
    cluster_type         similarity_cluster_type NOT NULL,
    n_images             int,
    n_objects            int,
    size_bytes           bigint,
    formed_by            clustering_method       NOT NULL
);
CREATE INDEX similarity_clusters_id_idx ON similarity_clusters (id);
CREATE INDEX similarity_clusters_dataset_id_idx ON similarity_clusters (dataset_id);

CREATE TABLE dataset_issues
(
    id           uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    type_id      int  NOT NULL,
    dataset_id   uuid NOT NULL,
    cluster_id   uuid NOT NULL UNIQUE,
    display_name text NOT NULL
);


CREATE TABLE label_categories
(
    id           uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    original_id  int  NOT NULL, -- to allow to trace back issues to user-supplied labels file
    display_name text NOT NULL,
    dataset_id   uuid NOT NULL
);

CREATE TABLE images
(
    id           uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    dataset_id   uuid NOT NULL,
    image_uri    text NOT NULL,
    original_uri text NOT NULL, -- map to the location within the source
    w            int  NOT NULL,
    h            int  NOT NULL,
    file_size    int  NOT NULL, -- in bytes
    mime_type    text NOT NULL,
    metadata     json,         -- some metadata here, not final, parts of it will be normalized to separate columns
    dir_path     text
);
CREATE INDEX images_dataset_id ON images (dataset_id);

CREATE TYPE label_type AS ENUM ('IMAGE', 'OBJECT');
CREATE TABLE labels
(
    id                    uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    original_id           bigint     NOT NULL, -- to allow to trace back issues to user-supplied labels file
    image_id              uuid       NOT NULL,
    dataset_id            uuid       NOT NULL,
    category_id           uuid       NOT NULL,
    category_display_name text       NOT NULL, -- denormalization
    type                  label_type NOT NULL,
    bounding_box          int[],
    source                metadata_source DEFAULT 'USER'
);
CREATE INDEX labels_image_id ON labels (image_id);
CREATE INDEX labels_category_display_name ON labels (category_display_name);
CREATE INDEX labels_dataset_id ON labels (dataset_id);

CREATE TABLE objects
(
    object_id  uuid NOT NULL,
    image_id   uuid NOT NULL,
    cluster_id uuid NOT NULL,
    dataset_id uuid NOT NULL
);
CREATE INDEX objects_object_id ON objects (object_id);
CREATE INDEX objects_image_id ON objects (image_id);
CREATE INDEX objects_cluster_id ON objects (cluster_id);

CREATE TABLE objects_to_images
(
    object_id    uuid NOT NULL UNIQUE,
    image_id     uuid NOT NULL,
    dataset_id   uuid NOT NULL,
    bounding_box integer[],
    dir_path     text
);
CREATE INDEX objects_to_images_image_id_idx ON objects_to_images (image_id);
CREATE INDEX objects_to_images_object_id_idx ON objects_to_images (object_id);

CREATE TABLE images_to_clusters
(
    cluster_id uuid NOT NULL,
    image_id   uuid NOT NULL,
    dataset_id uuid NOT NULL,
    CONSTRAINT cluster_image_unq UNIQUE (cluster_id, image_id)
);
CREATE INDEX images_to_clusters_cluster_id ON images_to_clusters (cluster_id);
CREATE INDEX images_to_clusters_image_id ON images_to_clusters (image_id);

CREATE TABLE image_similarity_mapping
(
    image_id         uuid NOT NULL,
    similar_image_id uuid NOT NULL,
    distance         float
);
CREATE INDEX image_similarity_mapping_image_id ON image_similarity_mapping (image_id);
CREATE INDEX image_similarity_mapping_image_similarity_mapping ON image_similarity_mapping (similar_image_id);

CREATE TABLE object_similarity_mapping
(
    object_id         uuid NOT NULL,
    similar_object_id uuid NOT NULL,
    distance          float
);
CREATE INDEX object_similarity_mapping_object_id ON object_similarity_mapping (object_id);
CREATE INDEX object_similarity_mapping_similar_object_id ON object_similarity_mapping (similar_object_id);

CREATE TABLE images_to_similarity_clusters
(
    cluster_id       uuid NOT NULL,
    image_id         uuid NOT NULL,
    dataset_id       uuid NOT NULL,
    order_in_cluster int,
    preview_order    int,
    CONSTRAINT similarity_cluster_image_unq UNIQUE (cluster_id, image_id)
);
CREATE INDEX images_to_similarity_clusters_cluster_id ON images_to_similarity_clusters (cluster_id);
CREATE INDEX images_to_similarity_clusters_image_id ON images_to_similarity_clusters (image_id);

CREATE TABLE objects_to_similarity_clusters
(
    cluster_id       uuid NOT NULL,
    object_id        uuid NOT NULL,
    dataset_id       uuid NOT NULL,
    order_in_cluster int,
    preview_order    int,
    CONSTRAINT similarity_cluster_object_unq UNIQUE (cluster_id, object_id)
);
CREATE INDEX objects_to_similarity_clusters_cluster_id ON objects_to_similarity_clusters (cluster_id);
CREATE INDEX objects_to_similarity_clusters_object_id ON objects_to_similarity_clusters (object_id);

-- The following enums are not required atm, but might be useful for more featureful ABAC
--CREATE TYPE access_effect AS ENUM ('Allow', 'Disallow');
CREATE TYPE access_operation AS ENUM (
    'READ',
    --'WRITE',
    'LIST',
    'UPDATE',
    'DELETE',
    'MANAGE_ACCESS',
    'SHARE_DATASETS');
--CREATE TYPE access_subject_type AS ENUM ('USER', 'ORGANIZATION');
--CREATE TYPE access_object_type AS ENUM ('DATASET', 'IMAGE');

CREATE TABLE access
(
    id         uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    subject_id uuid             NOT NULL, -- user_id
    -- subject_type access_subject_type NOT NULL, -- overkill atm.
    object_id  uuid             NOT NULL, -- dataset_id
    -- object_type access_object_type NOT NULL, -- overkill atm.
    operation  access_operation NOT NULL
    -- effect access_effect NOT NULL, -- overkill atm.
);
CREATE INDEX access_subject_id ON access (subject_id);
CREATE INDEX access_object_id ON access (object_id);
CREATE UNIQUE INDEX access_subject_object_op_idx ON access (subject_id, object_id, operation);

CREATE TABLE image_issues
(
    id          uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    type_id     int  NOT NULL,
    image_id    uuid NOT NULL,
    dataset_id  uuid NOT NULL,
    description text, -- an algo-generated free text describing this particular issue "instance"
    cause       uuid, -- most descriptive example of an issue cause is uuid of the label of a mislabeled object
    confidence  float,
    issue_subject_id uuid DEFAULT NULL
);
CREATE INDEX image_issues_image_id ON image_issues (image_id);
CREATE INDEX image_issues_cause ON image_issues (cause);

-- Initialize issue types
INSERT INTO issue_type
VALUES (0, 'mislabels', 0),
       (1, 'outliers', 0),
       (2, 'duplicates', 0),
       (3, 'blur', 1),
       (4, 'dark', 1),
       (5, 'bright', 2);

CREATE TABLE tags
(
    id   uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE media_to_tags
(
    media_id   uuid NOT NULL,
    dataset_id uuid NOT NULL,
    tag_id     uuid NOT NULL,
    -- column to state the time the row was added
    created_at timestamp DEFAULT now(),

    constraint media_to_tags_unq UNIQUE (media_id, dataset_id, tag_id)
);
CREATE INDEX media_to_tags_media_id ON media_to_tags (media_id);
CREATE INDEX media_to_tags_dataset_id ON media_to_tags (dataset_id);
CREATE INDEX media_to_tags_tag_id ON media_to_tags (tag_id);

CREATE TABLE media_to_captions
(
    media_id   uuid NOT NULL,
    dataset_id uuid NOT NULL,
    caption    text DEFAULT '',
    constraint media_to_captions_unq UNIQUE (media_id, dataset_id, caption)
);
CREATE INDEX media_to_captions_media_id ON media_to_captions (media_id);
CREATE INDEX media_to_captions_dataset_id ON media_to_captions (dataset_id);

CREATE SEQUENCE seq_flow_runs_id START 1;
CREATE TABLE flow_runs
(
    id       INTEGER PRIMARY KEY default nextval('seq_flow_runs_id'),
    settings json
);

CREATE TABLE flat_similarity_clusters
(
    image_uri            text,
    image_id             uuid,
    metadata             json,
    original_uri         text,
    bounding_box         integer[],
    image_or_object_id   uuid,
    cluster_id           uuid,
    dataset_id           uuid,
    preview_order        integer,
    display_name         text,
    cluster_type         similarity_cluster_type,
    n_images             integer,
    n_objects            integer,
    size_bytes           bigint,
    similarity_threshold similarity_threshold,
    labels               text[],
    issue_type_ids       integer[],
    caption              text,
    rank                 bigint,
    formed_by            clustering_method,
    dir_path             text,
    vl_labels            text[]
);
CREATE UNIQUE INDEX flat_similarity_clusters_cluster_id_image_or_object_id_idx
    ON flat_similarity_clusters (dataset_id, cluster_id, image_or_object_id);
CREATE INDEX flat_similarity_clusters_similarity_threshold_idx
    ON flat_similarity_clusters (similarity_threshold);

-- this index needs to be recreated every time after data is loaded into the table
-- PRAGMA create_fts_index(
-- 	flat_similarity_clusters, image_or_object_id, caption, labels, stemmer='porter',
-- 	stopwords='english', ignore='(\\.|[^a-z])+',
--     strip_accents=1, lower=1, overwrite=1
-- );

INSERT INTO users (user_identity, identity_provider, email, dataset_quota)
VALUES ('system', 'system', null, 1000),
       ('anonymous', 'system', null, 0)
ON CONFLICT DO NOTHING;


CREATE TABLE image_vector
(
    dataset_id         uuid,
    media_id           uuid,
    is_image           bool,
    embedding          float[576],
    primary key (dataset_id, media_id)
);

CREATE TABLE query_vector_embedding
(
    dataset_id        uuid,
    media_id          uuid,
    embedding         float[576],
    created_at        timestamp DEFAULT now(),
    created_by        uuid                NOT NULL,
    image_uri         text NOT NULL,
    bounding_box integer[4] DEFAULT NULL,
    filename          text NOT NULL
);

CREATE TABLE events
(
    serial_n   int,
    dataset_id uuid  NOT NULL,
    trans_id   int,
    event_type text  NOT NULL,
    event      json NOT NULL,
    CONSTRAINT dataset_id_serial_n_image_unq UNIQUE (dataset_id, serial_n)
);
CREATE INDEX events_dataset_id_idx on events(dataset_id);

CREATE TYPE export_task_status AS ENUM ('INIT', 'IN_PROGRESS', 'COMPLETED', 'FAILED');
CREATE TABLE export_task
(
    id          uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    dataset_id  uuid NOT NULL,
    user_id     uuid NOT NULL,
    created_at  timestamp DEFAULT now(),
    download_uri text DEFAULT NULL,
    progress    float default 0,
    status      export_task_status DEFAULT 'INIT'
);
CREATE INDEX export_task_dataset_id ON export_task (dataset_id);
CREATE INDEX export_task_user_id ON export_task (user_id);

ALTER TABLE users ADD COLUMN image_quota INTEGER;

CREATE TABLE user_groups
(
    id      uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    name    text UNIQUE NOT NULL
);

CREATE TABLE users_to_groups (
    user_id UUID NOT NULL REFERENCES users (id),
    group_id UUID NOT NULL REFERENCES user_groups (id),
    UNIQUE (user_id, group_id)
);

INSERT INTO user_groups (name)
VALUES ('administrators')
ON CONFLICT (name) DO NOTHING;

INSERT INTO users_to_groups (user_id, group_id)
SELECT users.id, user_groups.id
FROM users, user_groups
WHERE users.user_identity = 'system'
  AND users.identity_provider = 'system'
  AND user_groups.name = 'administrators'
ON CONFLICT (user_id, group_id) DO NOTHING;

INSERT INTO access (subject_id, object_id, operation)
SELECT user_groups.id, datasets.id, 'MANAGE_ACCESS'
FROM datasets, user_groups
WHERE user_groups.name = 'administrators'
ON CONFLICT (subject_id, object_id, operation) DO NOTHING;
