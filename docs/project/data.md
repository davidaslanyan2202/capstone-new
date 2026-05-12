# Data Connection Plan

## 1. Goal

Build one useful final table for future analytics:

`data/processed/player_season_analytics.csv`

The final table should have one row per player-season/team record and include:

- Performance metrics from `metrics.csv`
- Transfermarkt player ID
- Season-end market value target
- Contract expiry features
- Transfer-history summary features

## 2. Data Sources

### Base Table: `data/interim/metrics.csv`

Use this as the main table.

Important columns:

- `Player`
- `Nation`
- `Pos`
- `Squad`
- `Comp`
- `Age`
- `season`
- Performance metrics such as `Min`, `90s`, `Gls`, `Ast`, `Sh`, `SoT`, `Crs`, `Int`, `TklW`
- `trmrkt_player_id`

Current coverage:

- 6,471 rows
- 2,821 unique Transfermarkt player IDs

Recommended row grain:

- One row per `trmrkt_player_id` + `season` + `Squad` + `Comp`

This handles players who changed clubs during a season.

### Transfer History: `data/scraped/transfermarkt/history_json/*.json`

Each file is named by Transfermarkt player ID:

`data/scraped/transfermarkt/history_json/{trmrkt_player_id}.json`

Current coverage:

- 2,821 JSON files
- 2,821 matching IDs from `metrics.csv`
- 28,746 transfer records
- 20,621 records with non-null `contractUntilDate`

Important JSON path:

- `data.history.terminated`
- `data.history.pending`

Most analytics should start with `terminated` records because they are completed transfer events.

Useful fields inside each transfer record:

- `id`
- `details.playerId`
- `details.date`
- `details.contractUntilDate`
- `details.seasonId`
- `details.marketValue.value`
- `details.fee.value`
- `details.fee.compact.content`
- `details.age`
- `details.remainingContractPeriod`
- `details.season.display`
- `transferSource.clubId`
- `transferSource.competitionId`
- `transferSource.countryId`
- `transferDestination.clubId`
- `transferDestination.competitionId`
- `transferDestination.countryId`
- `typeDetails.type`
- `relativeUrl`

### Market Values CSV

Use `player_values.csv` or `player_values_old.csv`, whichever is the final trusted historical value file.

Expected important columns:

- `player_id`
- `date_unix`
- `value`
- `player_name`

This source should provide the target market value for each row in `metrics.csv`.

## 3. Recommended Intermediate Tables

### 1. `data/interim/transfer_history_events.csv`

Flatten all JSON files into one event table.

Recommended columns:

- `trmrkt_player_id`
- `transfer_id`
- `event_bucket`
- `is_pending`
- `transfer_type`
- `transfer_date`
- `season_id`
- `season_display`
- `contract_until_date`
- `remaining_contract_period_raw`
- `age_at_transfer`
- `market_value_eur_at_transfer`
- `fee_eur`
- `fee_text`
- `source_club_id`
- `source_competition_id`
- `source_country_id`
- `destination_club_id`
- `destination_competition_id`
- `destination_country_id`
- `relative_url`

Recommended transformations:

- Parse ISO transfer dates into dates.
- Parse `contractUntilDate` into dates.
- Store market value and fee as numeric EUR fields where possible.
- Keep `fee_text` because many fees are text values such as free transfer, loan, or unknown.

### 2. `data/interim/player_season_market_values.csv`

Create one market value target per row in `metrics.csv`.

Recommended columns:

- `trmrkt_player_id`
- `season`
- `Squad`
- `Comp`
- `valuation_date`
- `market_value_eur`
- `market_value_date`
- `market_value_days_from_valuation`
- `log_market_value_eur`

Recommended valuation dates:

- `21/22` -> `2022-06-30`
- `22/23` -> `2023-06-30`
- `23/24` -> `2024-06-30`

Recommended matching rule:

1. For each player-season, find values for the same `trmrkt_player_id`.
2. Prefer values between May 15 and August 31 of the season-ending year.
3. Select the value closest to `valuation_date`.
4. If none exists in the window, select the closest available value and flag it.

Recommended extra columns:

- `market_value_in_window`
- `market_value_missing`

### 3. `data/interim/player_season_contract_features.csv`

Create one contract row per `metrics.csv` row.

Recommended columns:

- `trmrkt_player_id`
- `season`
- `Squad`
- `Comp`
- `valuation_date`
- `latest_transfer_id_before_valuation`
- `latest_transfer_date_before_valuation`
- `latest_transfer_type_before_valuation`
- `contract_until_date`
- `contract_days_remaining`
- `contract_years_remaining`
- `contract_expiring_within_1y`
- `contract_expiring_within_2y`
- `contract_missing`
- `days_since_last_transfer`
- `last_transfer_market_value_eur`
- `last_transfer_fee_eur`
- `last_transfer_fee_text`

Recommended matching rule:

1. For each `metrics.csv` row, use the same `trmrkt_player_id`.
2. Keep only transfer-history events where `transfer_date <= valuation_date`.
3. Prefer completed `terminated` events.
4. Select the most recent event before valuation.
5. Use that event's `contract_until_date` as the best available contract expiry.
6. Calculate remaining contract time from `valuation_date`.

Important:

Never use transfer events after the valuation date as model features. That would leak future information into the model.

## 4. Final Table Design

### Output

`data/processed/player_season_analytics.csv`

### Join Keys

Primary join keys:

- `trmrkt_player_id`
- `season`
- `Squad`
- `Comp`

If market values or contract features are generated directly from each `metrics.csv` row, add a synthetic `row_id` first and use that as the safest join key.

Recommended `row_id` format:

`{trmrkt_player_id}_{season}_{Squad}_{Comp}_{row_number}`

### Final Column Groups

Identity:

- `row_id`
- `trmrkt_player_id`
- `Player`
- `Nation`
- `Pos`
- `position_group`
- `Squad`
- `Comp`
- `season`
- `valuation_date`

Performance:

- Original performance columns from `metrics.csv`
- Per-90 versions for count stats
- Minutes threshold flags

Market value target:

- `market_value_eur`
- `market_value_date`
- `market_value_days_from_valuation`
- `market_value_in_window`
- `log_market_value_eur`

Contract:

- `contract_until_date`
- `contract_days_remaining`
- `contract_years_remaining`
- `contract_expiring_within_1y`
- `contract_expiring_within_2y`
- `contract_missing`

Transfer history:

- `latest_transfer_date_before_valuation`
- `latest_transfer_type_before_valuation`
- `days_since_last_transfer`
- `last_transfer_market_value_eur`
- `last_transfer_fee_eur`
- `last_transfer_fee_text`

Model helper fields:

- `age_squared`
- `minutes_bucket`
- `season_end_year`
- Cleaned league name
- Cleaned nation

## 5. Useful Feature Ideas

### Contract Features

- `contract_years_remaining`
- `contract_expiring_within_1y`
- `contract_expiring_within_2y`
- `contract_missing`
- `contract_expired_or_unknown`

### Transfer History Features

- `days_since_last_transfer`
- `last_transfer_was_loan`
- `last_transfer_was_free`
- `last_transfer_fee_eur`
- `last_transfer_market_value_eur`
- `transfer_count_before_valuation`
- `loan_count_before_valuation`

### Performance Features

Use per-90 rates for count stats:

- `goals_per90`
- `assists_per90`
- `shots_per90`
- `shots_on_target_per90`
- `crosses_per90`
- `interceptions_per90`
- `tackles_won_per90`
- `fouls_per90`
- `fouled_per90`

Keep volume or reliability features:

- `Min`
- `Starts`
- `90s`
- `low_minutes_flag`

## 6. Quality Checks

Before modeling, check:

- Every row has a non-empty `trmrkt_player_id`.
- Every row has a `valuation_date`.
- Market value target coverage is high.
- Contract feature coverage is documented.
- No contract or transfer event after `valuation_date` is used as a feature.
- Duplicate rows are intentional and tied to multiple squads or competitions.
- Numeric columns are actually numeric.
- `market_value_eur` has no zero values unless intentionally allowed.
- `log_market_value_eur` is present for all modeling rows.

## 7. Recommended Build Order

1. Parse JSON files into `transfer_history_events.csv`.
2. Add `row_id` and `valuation_date` to `metrics.csv`.
3. Build `player_season_market_values.csv`.
4. Build `player_season_contract_features.csv`.
5. Join everything into `player_season_analytics.csv`.
6. Run data quality checks.
7. Start EDA and modeling from `player_season_analytics.csv`.
