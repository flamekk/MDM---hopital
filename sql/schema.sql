-- Projection PostgreSQL 17+ du hub. La démo Streamlit reste sur SQLite.
CREATE SCHEMA IF NOT EXISTS mdm;
CREATE TABLE IF NOT EXISTS mdm.run (
  run_id UUID PRIMARY KEY, created_at TIMESTAMPTZ NOT NULL,
  rules_version VARCHAR(30) NOT NULL, method VARCHAR(30) NOT NULL,
  source_fingerprint CHAR(64) NOT NULL, snapshot JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS mdm.master_entity (
  run_id UUID NOT NULL REFERENCES mdm.run, master_id UUID NOT NULL,
  domain VARCHAR(20) NOT NULL CHECK(domain IN ('patient','personnel','produit')),
  status VARCHAR(20) NOT NULL CHECK(status='ACTIVE'),
  member_count INTEGER NOT NULL CHECK(member_count > 0),
  source_count INTEGER NOT NULL CHECK(source_count > 0),
  qualified_id VARCHAR(150), id_issuer VARCHAR(150),
  PRIMARY KEY(run_id, master_id), UNIQUE(run_id, master_id, domain)
);
CREATE TABLE IF NOT EXISTS mdm.patient_master (
  run_id UUID NOT NULL, master_id UUID NOT NULL,
  domain VARCHAR(20) NOT NULL DEFAULT 'patient' CHECK(domain='patient'),
  family_name VARCHAR(150), given_names VARCHAR(150), birth_date DATE,
  phone VARCHAR(32), email VARCHAR(254), address VARCHAR(500),
  PRIMARY KEY(run_id, master_id),
  FOREIGN KEY(run_id,master_id,domain) REFERENCES mdm.master_entity(run_id,master_id,domain)
);
CREATE TABLE IF NOT EXISTS mdm.personnel_master (
  run_id UUID NOT NULL, master_id UUID NOT NULL,
  domain VARCHAR(20) NOT NULL DEFAULT 'personnel' CHECK(domain='personnel'),
  family_name VARCHAR(150), given_names VARCHAR(150), professional_category VARCHAR(30),
  email VARCHAR(254), phone VARCHAR(32), PRIMARY KEY(run_id,master_id),
  FOREIGN KEY(run_id,master_id,domain) REFERENCES mdm.master_entity(run_id,master_id,domain)
);
CREATE TABLE IF NOT EXISTS mdm.product_master (
  run_id UUID NOT NULL, master_id UUID NOT NULL,
  domain VARCHAR(20) NOT NULL DEFAULT 'produit' CHECK(domain='produit'),
  preferred_name VARCHAR(250), category VARCHAR(30), manufacturer VARCHAR(200),
  model_reference VARCHAR(100), dosage VARCHAR(100), form VARCHAR(100),
  package_quantity DECIMAL(12,3) CHECK(package_quantity > 0), package_unit VARCHAR(20),
  sterile VARCHAR(20) CHECK(sterile IN ('oui','non','inconnu')),
  PRIMARY KEY(run_id,master_id),
  FOREIGN KEY(run_id,master_id,domain) REFERENCES mdm.master_entity(run_id,master_id,domain)
);
CREATE TABLE IF NOT EXISTS mdm.source_link (
  run_id UUID NOT NULL, domain VARCHAR(20) NOT NULL, source VARCHAR(100) NOT NULL,
  local_id VARCHAR(150) NOT NULL, rid VARCHAR(24) NOT NULL, master_id UUID NOT NULL,
  PRIMARY KEY(run_id,domain,source,local_id),
  FOREIGN KEY(run_id,master_id,domain) REFERENCES mdm.master_entity(run_id,master_id,domain)
);
CREATE TABLE IF NOT EXISTS mdm.attribute_provenance (
  run_id UUID NOT NULL, master_id UUID NOT NULL, field VARCHAR(100) NOT NULL,
  value TEXT, selected_source VARCHAR(100), selected_local_id VARCHAR(150),
  policy TEXT NOT NULL, conflict BOOLEAN NOT NULL, candidates JSONB NOT NULL,
  PRIMARY KEY(run_id,master_id,field),
  FOREIGN KEY(run_id,master_id) REFERENCES mdm.master_entity(run_id,master_id)
);
CREATE TABLE IF NOT EXISTS mdm.related_record (
  run_id UUID NOT NULL, relation_type VARCHAR(50) NOT NULL, ordinal INTEGER NOT NULL,
  master_id UUID NOT NULL, payload JSONB NOT NULL,
  PRIMARY KEY(run_id,relation_type,ordinal),
  FOREIGN KEY(run_id,master_id) REFERENCES mdm.master_entity(run_id,master_id)
);
CREATE INDEX IF NOT EXISTS source_link_master_idx ON mdm.source_link(run_id,master_id);
CREATE INDEX IF NOT EXISTS patient_name_idx ON mdm.patient_master(family_name,given_names);
