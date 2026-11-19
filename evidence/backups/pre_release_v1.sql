BEGIN TRANSACTION;
CREATE TABLE audit(
                id INTEGER PRIMARY KEY,
                ticket_id INTEGER,
                from_state TEXT,
                to_state TEXT,
                actor TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
INSERT INTO "audit" VALUES(1,1,'New','Assigned','technician','2026-11-19 17:09:09');
INSERT INTO "audit" VALUES(2,1,'Assigned','In Progress','technician','2026-11-19 17:09:09');
INSERT INTO "audit" VALUES(3,1,'In Progress','Resolved','technician','2026-11-19 17:09:09');
CREATE TABLE bookings(
                id INTEGER PRIMARY KEY,
                facility TEXT,
                start_min INTEGER,
                end_min INTEGER,
                status TEXT,
                requester TEXT DEFAULT 'faculty',
                campus_code TEXT DEFAULT 'MAIN_CAMPUS',
                policy_version TEXT DEFAULT 'v1',
                sync_status TEXT DEFAULT 'Pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
INSERT INTO "bookings" VALUES(1,'Lab-204',540,660,'Approved','dr_sharma','MAIN_CAMPUS','v1','Synced','2026-11-19 17:09:09');
INSERT INTO "bookings" VALUES(2,'Cryo-Annex-01',660,860,'Pending','dr_sharma','RESEARCH_ANNEX','v2','Synced','2026-11-19 17:09:09');
CREATE TABLE integration_outbox(
                id INTEGER PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                target_system TEXT NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'Pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                next_retry_at TEXT,
                remote_id TEXT,
                last_error TEXT
            );
INSERT INTO "integration_outbox" VALUES(1,'booking',1,'calendar','cal-booking-1','Synced',1,'2026-11-19T17:09:09.861947+00:00','CALENDAR-BOOKING-1',NULL);
INSERT INTO "integration_outbox" VALUES(2,'booking',2,'calendar','cal-booking-2','Synced',1,'2026-11-19T17:09:09.878068+00:00','CALENDAR-BOOKING-2',NULL);
INSERT INTO "integration_outbox" VALUES(3,'ticket',1,'issue-tracker','issue-sensor-sensor-204-evt-pre-v1','Synced',1,'2026-11-19T17:09:09.900458+00:00','ISSUE-TRACKER-TICKET-1',NULL);
CREATE TABLE policies(
                campus_code TEXT PRIMARY KEY,
                policy_version TEXT NOT NULL,
                max_duration INTEGER NOT NULL,
                temp_limit REAL NOT NULL
            );
INSERT INTO "policies" VALUES('MAIN_CAMPUS','v1',180,28.0);
INSERT INTO "policies" VALUES('RESEARCH_ANNEX','v2',240,24.5);
CREATE TABLE tickets(
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                state TEXT NOT NULL,
                version INTEGER NOT NULL,
                notes TEXT,
                source TEXT,
                event_id TEXT,
                priority TEXT DEFAULT 'M3',
                category TEXT DEFAULT 'Manual Review',
                campus_code TEXT DEFAULT 'MAIN_CAMPUS',
                policy_version TEXT DEFAULT 'v1',
                sync_status TEXT DEFAULT 'Pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, event_id)
            );
INSERT INTO "tickets" VALUES(1,'HVAC temperature alert (29.8C) in Lab-204','Resolved',4,'Calibrated chiller','sensor-204','evt-pre-v1','M1','HVAC','MAIN_CAMPUS','v1','Synced','2026-11-19 17:09:09');
COMMIT;
