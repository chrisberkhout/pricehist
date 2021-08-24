-- Created by pricehist {version} at {timestamp}

BEGIN;

-- The GnuCash database must already have entries for the relevant commodities.
-- These statements fail and later changes are skipped if that isn't the case.
CREATE TEMPORARY TABLE guids (mnemonic TEXT NOT NULL, guid TEXT NOT NULL);
INSERT INTO guids VALUES ({base}, (SELECT guid FROM commodities WHERE mnemonic = {base} LIMIT 1));
INSERT INTO guids VALUES ({quote}, (SELECT guid FROM commodities WHERE mnemonic = {quote} LIMIT 1));

-- Create a staging table for the new price data.
-- Doing this via a SELECT ensures the correct date type across databases.
CREATE TEMPORARY TABLE new_prices AS
SELECT p.guid, p.date, c.mnemonic AS base, c.mnemonic AS quote, p.source, p.type, p.value_num, p.value_denom
FROM prices p, commodities c
WHERE FALSE;

-- Populate the staging table.
{values_comment}INSERT INTO new_prices (guid, date, base, quote, source, type, value_num, value_denom) VALUES
{values_comment}{values}
{values_comment};

-- Get some numbers for the summary.
CREATE TEMPORARY TABLE summary (description TEXT, num INT);
INSERT INTO summary VALUES ('staged rows', (SELECT COUNT(*) FROM new_prices));
INSERT INTO summary VALUES ('pre-existing rows', (SELECT COUNT(*) FROM new_prices tp, prices p where p.guid = tp.guid));
INSERT INTO summary VALUES ('additional rows', (SELECT COUNT(*) FROM new_prices WHERE guid NOT IN (SELECT guid FROM prices)));

-- Insert the new prices into the prices table, unless they're already there.
INSERT INTO prices (guid, commodity_guid, currency_guid, date, source, type, value_num, value_denom)
SELECT tp.guid, g1.guid, g2.guid, tp.date, tp.source, tp.type, tp.value_num, tp.value_denom
FROM new_prices tp, guids g1, guids g2
WHERE tp.base = g1.mnemonic
  AND tp.quote = g2.mnemonic
  AND tp.guid NOT IN (SELECT guid FROM prices)
;

-- Show the final relevant rows of the main prices table
SELECT 'final' AS status, p.* FROM prices p WHERE p.guid IN (SELECT guid FROM new_prices) ORDER BY p.date;

-- Show the summary.
SELECT * FROM summary;

COMMIT;
