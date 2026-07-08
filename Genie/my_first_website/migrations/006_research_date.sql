-- 006_research_date.sql
-- Adds a research date to research_reports for the date-sorted list view.
-- Existing rows are backfilled to the migration date; the report form lets
-- the user correct individual dates afterwards.
-- Additive only — no existing data is modified beyond the NULL backfill.

ALTER TABLE research_reports ADD COLUMN IF NOT EXISTS research_date DATE;
UPDATE research_reports SET research_date = CURRENT_DATE WHERE research_date IS NULL;
