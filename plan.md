# Project Plan

## 1. Current Goal

The project will build an analytics-ready player-season dataset for football player valuation. The final table should combine:

- Season-level performance metrics
- Transfermarkt player IDs
- Historical market value observations
- Transfer-history events from downloaded JSON files
- Contract-related fields where available

The modeling goal remains the same: predict and explain football player market value using performance, age, position, league context, and contract situation.

## 2. Current Data Assets

### `data/processed/metrics.csv`

This is now the main performance table.

Current role:

- One row per player-season/team record
- Contains performance columns from `top5.csv`
- Contains `trmrkt_player_id`, which is the main join key for Transfermarkt data

Observed coverage:

- Rows: 6,471
- Unique `trmrkt_player_id`: 2,821
- Seasons: 2021/22, 2022/23, 2023/24
- Leagues: Premier League, Ligue 1, Bundesliga, Serie A, La Liga

This file should be treated as the base table for future analytics.

### `jsons/*.json`

These are downloaded Transfermarkt transfer-history API responses.

Observed coverage:

- JSON files: 2,821
- Matches the 2,821 unique player IDs in `metrics.csv`
- Transfer records found: 28,746
- Files with transfer records: 2,821
- `contractUntilDate` is non-null in 20,621 transfer records

Useful JSON fields:

- `data.playerId`
- `data.history.terminated`
- `data.history.pending`
- Transfer event ID
- Transfer date
- Contract-until date
- Season ID and season display
- Market value at transfer
- Transfer fee where available
- Source club, source competition, source country
- Destination club, destination competition, destination country
- Transfer type, such as standard transfer, loan, or loan return

Important limitation:

The JSON files provide transfer-event-level contract data, not a clean season-by-season contract table. We need to transform events into player-season features carefully.

### `data/raw/player_values_old.csv`

Current role:

- Used to match names and assign `trmrkt_player_id`

Possible future role:

- Can still help as a historical market-value source if it contains broad dated value snapshots.

### `data/raw/player_values.csv`

If this file is kept in the repo, it should be used as the main historical market-value table because it has dated value observations by player ID.

Recommended role:

- Create one target market value per player-season by selecting the nearest valid value observation around the chosen season-end date.

## 3. Data Still Missing Or Weak

### Still Needed

1. A final target-value rule

   We need one target value for each player-season in `metrics.csv`.

   Recommended rule:

   - For 2021/22, use nearest market value around 2022-06-30.
   - For 2022/23, use nearest market value around 2023-06-30.
   - For 2023/24, use nearest market value around 2024-06-30.

   Use a search window such as May 15 to August 31. If no value exists in that window, keep the closest observation and add a distance-in-days audit column.

2. A clean contract feature rule

   The transfer-history JSON gives contract expiry on many transfer events. We need to decide how to map that to a player-season.

   Recommended rule:

   - For each player-season valuation date, use the most recent transfer-history event on or before the valuation date.
   - Take its `contractUntilDate` as the best available contract expiry.
   - Calculate `contract_years_remaining` from valuation date to contract expiry.
   - Add flags for missing contract expiry and contract expiring soon.

3. Stronger performance features

   Current performance data is useful but does not include important modern football features such as xG, xA, passing, progression, shot-creating actions, carries, pressures, blocks, clearances, aerials, or goalkeeper data.

### Nice To Have

- Exact birth date rather than age/birth year
- Club strength or final league position
- Actual team table position and points
- European competition participation
- Injury history
- Actual transfer fees for validation against market values

## 4. Recommended Data Pipeline

### Step 1: Treat `metrics.csv` As The Base Table

Keep one row per player-season/team record from `metrics.csv`.

Primary key candidate:

- `trmrkt_player_id`
- `season`
- `Squad`
- `Comp`

If a player has multiple squads in one season, keep separate rows unless you intentionally aggregate to one player-season.

### Step 2: Parse Transfer-History JSONs

Create a normalized event table:

`data/processed/transfer_history_events.csv`

Recommended columns:

- `trmrkt_player_id`
- `transfer_id`
- `event_status`
- `transfer_type`
- `transfer_date`
- `season_id`
- `season_display`
- `contract_until_date`
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

Include both `terminated` and `pending` events, but default analytics should probably use only non-pending completed transfers.

### Step 3: Create Season Valuation Dates

Add a `valuation_date` column to `metrics.csv`.

Recommended mapping:

- `21/22` -> `2022-06-30`
- `22/23` -> `2023-06-30`
- `23/24` -> `2024-06-30`

This date becomes the anchor for market value and contract features.

### Step 4: Join Historical Market Values

Use the market-value CSV to create:

`data/processed/player_season_market_values.csv`

For each `trmrkt_player_id` and `valuation_date`:

- Find the nearest value observation in the selected window
- Save `market_value_eur`
- Save `market_value_date`
- Save `market_value_days_from_valuation`
- Save `log_market_value_eur`

The modeling target should usually be `log_market_value_eur`.

### Step 5: Join Contract Features

Use the parsed transfer-history event table.

For each row in `metrics.csv`:

- Filter transfer events for the same `trmrkt_player_id`
- Keep events with `transfer_date <= valuation_date`
- Pick the most recent event
- Read `contract_until_date`
- Calculate contract features

Recommended columns:

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

Important caution:

Do not use transfer events after the valuation date as model features. That would leak future information.

### Step 6: Build Final Analytics Table

Create:

`data/processed/player_season_analytics.csv`

This should combine:

- Base metrics from `metrics.csv`
- Market-value target columns
- Contract features
- Transfer-history summary features
- Cleaned categorical columns
- Engineered per-90 and age features

Recommended target column:

- `log_market_value_eur`

Recommended important feature groups:

- Player context: age, position, nation
- Team/league context: squad, competition, season
- Playing time: minutes, starts, 90s
- Performance: goals, assists, shots, shots on target, crosses, interceptions, tackles won
- Discipline: yellow/red cards, fouls
- Contract: years remaining, expiring soon flags, missing-contract flag
- Transfer history: days since last transfer, last fee, last transfer market value, transfer type

## 5. Modeling Steps

1. Build the final analytics table.
2. Run missingness and outlier checks.
3. Decide whether to filter low-minute players.
4. Train a baseline model predicting average log market value.
5. Train interpretable regression models.
6. Train tree-based models.
7. Compare global model vs position-specific models.
8. Interpret feature importance and contract effects.
9. Report errors by league, position, age group, and season.

Recommended train/test split:

- Train: 2021/22 and 2022/23
- Test: 2023/24

Recommended metrics:

- RMSE on log market value
- MAE on log market value
- R^2
- Optional MAE in euros after inverse transform

## 6. Immediate Next Actions

1. Create a parser for `jsons/*.json` into `transfer_history_events.csv`.
2. Create a valuation-date column for each `metrics.csv` row.
3. Build season-level market-value targets.
4. Build contract features using only transfer events before valuation date.
5. Save the final `player_season_analytics.csv`.
6. Start EDA and baseline modeling.
