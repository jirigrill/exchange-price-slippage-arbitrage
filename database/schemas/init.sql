-- TimescaleDB initialization script for Bitcoin Arbitrage Monitor
-- This script creates the database schema with hypertables optimized for time-series data

-- Create extension if not exists
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create exchange_prices table for storing price data from all exchanges
CREATE TABLE IF NOT EXISTS exchange_prices (
    id SERIAL,
    exchange_name VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(15,8) NOT NULL,
    price_usd DECIMAL(15,8) NOT NULL,
    original_currency VARCHAR(10) NOT NULL,
    volume DECIMAL(20,8) DEFAULT 0,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Add constraints
    CONSTRAINT exchange_prices_price_positive CHECK (price > 0),
    CONSTRAINT exchange_prices_price_usd_positive CHECK (price_usd > 0),
    CONSTRAINT exchange_prices_volume_non_negative CHECK (volume >= 0)
);

-- Convert to hypertable partitioned by timestamp (1 day chunks)
SELECT create_hypertable('exchange_prices', 'timestamp', 
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_exchange_prices_exchange_timestamp 
    ON exchange_prices (exchange_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_exchange_prices_symbol_timestamp 
    ON exchange_prices (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_exchange_prices_timestamp 
    ON exchange_prices (timestamp DESC);

-- Create arbitrage_opportunities table for detected opportunities
CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
    id SERIAL,
    buy_exchange VARCHAR(50) NOT NULL,
    sell_exchange VARCHAR(50) NOT NULL,
    buy_price DECIMAL(15,8) NOT NULL,
    sell_price DECIMAL(15,8) NOT NULL,
    profit_usd DECIMAL(15,8) NOT NULL,
    profit_percentage DECIMAL(8,4) NOT NULL,
    volume_limit DECIMAL(20,8) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Add constraints
    CONSTRAINT arbitrage_profit_positive CHECK (profit_usd > 0),
    CONSTRAINT arbitrage_percentage_positive CHECK (profit_percentage > 0),
    CONSTRAINT arbitrage_sell_higher CHECK (sell_price > buy_price)
);

-- Convert to hypertable
SELECT create_hypertable('arbitrage_opportunities', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indexes for arbitrage opportunities
CREATE INDEX IF NOT EXISTS idx_arbitrage_timestamp 
    ON arbitrage_opportunities (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_arbitrage_profit_percentage 
    ON arbitrage_opportunities (profit_percentage DESC, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_arbitrage_exchanges 
    ON arbitrage_opportunities (buy_exchange, sell_exchange, timestamp DESC);

-- Create exchange_status table for monitoring exchange health
CREATE TABLE IF NOT EXISTS exchange_status (
    id SERIAL,
    exchange_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'active', 'error', 'timeout'
    error_message TEXT,
    response_time_ms INTEGER,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Add constraints
    CONSTRAINT exchange_status_valid CHECK (status IN ('active', 'error', 'timeout')),
    CONSTRAINT response_time_non_negative CHECK (response_time_ms IS NULL OR response_time_ms >= 0)
);

-- Convert to hypertable
SELECT create_hypertable('exchange_status', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Create index for exchange status
CREATE INDEX IF NOT EXISTS idx_exchange_status_exchange_timestamp 
    ON exchange_status (exchange_name, timestamp DESC);

-- Create aggregation views for analytics

-- Latest prices view
CREATE OR REPLACE VIEW latest_exchange_prices AS
SELECT DISTINCT ON (exchange_name, symbol)
    exchange_name,
    symbol,
    price,
    price_usd,
    original_currency,
    volume,
    timestamp
FROM exchange_prices
ORDER BY exchange_name, symbol, timestamp DESC;

-- Convenience view for local timezone display (configurable offset)
-- Note: This uses a 2-hour offset as example - adjust INTERVAL based on your timezone
CREATE OR REPLACE VIEW exchange_prices_local AS
SELECT 
    id,
    exchange_name,
    symbol,
    price,
    price_usd,
    original_currency,
    volume,
    (timestamp + INTERVAL '2 hours')::timestamp as local_timestamp,
    timestamp as utc_timestamp,
    (created_at + INTERVAL '2 hours')::timestamp as local_created_at
FROM exchange_prices;

-- Similarly for arbitrage opportunities
CREATE OR REPLACE VIEW arbitrage_opportunities_local AS
SELECT 
    id,
    buy_exchange,
    sell_exchange,
    buy_price,
    sell_price,
    profit_usd,
    profit_percentage,
    volume_limit,
    (timestamp + INTERVAL '2 hours')::timestamp as local_timestamp,
    timestamp as utc_timestamp,
    (created_at + INTERVAL '2 hours')::timestamp as local_created_at
FROM arbitrage_opportunities;

-- Price spreads view (current)
CREATE OR REPLACE VIEW current_price_spreads AS
WITH latest_prices AS (
    SELECT exchange_name, price_usd, timestamp
    FROM latest_exchange_prices
    WHERE symbol LIKE '%BTC%'
),
price_stats AS (
    SELECT 
        MIN(price_usd) as min_price,
        MAX(price_usd) as max_price,
        COUNT(*) as exchange_count,
        MAX(timestamp) as latest_timestamp
    FROM latest_prices
)
SELECT 
    min_price,
    max_price,
    (max_price - min_price) as spread_usd,
    CASE 
        WHEN min_price > 0 THEN ((max_price - min_price) / min_price) * 100
        ELSE 0
    END as spread_percentage,
    exchange_count,
    latest_timestamp
FROM price_stats
WHERE exchange_count >= 2;

-- Create continuous aggregates for better query performance

-- Hourly price aggregates
SELECT add_continuous_aggregate_policy('price_1h',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Create materialized view for hourly aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS price_1h
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', timestamp) AS bucket,
    exchange_name,
    symbol,
    FIRST(price_usd, timestamp) as open_price,
    MAX(price_usd) as high_price,
    MIN(price_usd) as low_price,
    LAST(price_usd, timestamp) as close_price,
    AVG(price_usd) as avg_price,
    SUM(volume) as total_volume,
    COUNT(*) as data_points
FROM exchange_prices
GROUP BY bucket, exchange_name, symbol;

-- Daily arbitrage opportunity summary
CREATE MATERIALIZED VIEW IF NOT EXISTS arbitrage_daily
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', timestamp) AS bucket,
    buy_exchange,
    sell_exchange,
    COUNT(*) as opportunity_count,
    AVG(profit_percentage) as avg_profit_percentage,
    MAX(profit_percentage) as max_profit_percentage,
    SUM(profit_usd) as total_profit_usd
FROM arbitrage_opportunities
GROUP BY bucket, buy_exchange, sell_exchange;

-- Add retention policies (optional - keep data for 30 days by default)
-- Uncomment these lines if you want automatic data cleanup:
-- SELECT add_retention_policy('exchange_prices', INTERVAL '30 days');
-- SELECT add_retention_policy('arbitrage_opportunities', INTERVAL '30 days');
-- SELECT add_retention_policy('exchange_status', INTERVAL '7 days');

-- Create helper functions

-- Function to get latest prices for all exchanges
CREATE OR REPLACE FUNCTION get_latest_prices()
RETURNS TABLE(exchange_name TEXT, symbol TEXT, price_usd DECIMAL, timestamp TIMESTAMPTZ) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ON (ep.exchange_name, ep.symbol)
        ep.exchange_name::TEXT,
        ep.symbol::TEXT,
        ep.price_usd,
        ep.timestamp
    FROM exchange_prices ep
    ORDER BY ep.exchange_name, ep.symbol, ep.timestamp DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get price spread for a time period
CREATE OR REPLACE FUNCTION get_price_spread_history(hours INTEGER DEFAULT 24)
RETURNS TABLE(
    bucket TIMESTAMPTZ,
    min_price DECIMAL,
    max_price DECIMAL,
    spread_usd DECIMAL,
    spread_percentage DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        time_bucket('1 hour', ep.timestamp) as bucket,
        MIN(ep.price_usd) as min_price,
        MAX(ep.price_usd) as max_price,
        (MAX(ep.price_usd) - MIN(ep.price_usd)) as spread_usd,
        CASE 
            WHEN MIN(ep.price_usd) > 0 THEN ((MAX(ep.price_usd) - MIN(ep.price_usd)) / MIN(ep.price_usd)) * 100
            ELSE 0
        END as spread_percentage
    FROM exchange_prices ep
    WHERE ep.timestamp >= NOW() - (hours || ' hours')::INTERVAL
        AND ep.symbol LIKE '%BTC%'
    GROUP BY bucket
    ORDER BY bucket DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to arbitrage user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO arbitrage_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO arbitrage_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO arbitrage_user;

-- Insert initial test data (optional)
-- INSERT INTO exchange_prices (exchange_name, symbol, price, price_usd, original_currency)
-- VALUES 
--     ('kraken', 'BTC/USD', 45000.00, 45000.00, 'USD'),
--     ('coinmate', 'BTC/CZK', 1100000.00, 45500.00, 'CZK');

COMMIT;