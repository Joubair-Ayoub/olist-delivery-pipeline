CREATE SCHEMA IF NOT EXISTS olist;
CREATE TABLE IF NOT EXISTS olist.customers (
 customer_id text PRIMARY KEY, customer_unique_id text NOT NULL,
 customer_city text NOT NULL, customer_state text NOT NULL
);
CREATE TABLE IF NOT EXISTS olist.orders (
 order_id text PRIMARY KEY, customer_id text NOT NULL REFERENCES olist.customers,
 order_status text NOT NULL, order_purchase_timestamp timestamp NOT NULL,
 order_delivered_customer_date timestamp,
 order_estimated_delivery_date timestamp NOT NULL
);
CREATE TABLE IF NOT EXISTS olist.order_items (
 order_id text REFERENCES olist.orders, order_item_id integer CHECK(order_item_id>0),
 product_id text NOT NULL, price numeric(14,2) NOT NULL CHECK(price>=0),
 freight_value numeric(14,2) NOT NULL CHECK(freight_value>=0),
 PRIMARY KEY(order_id, order_item_id)
);
CREATE OR REPLACE VIEW olist.delivery_analysis AS
WITH amounts AS (
 SELECT order_id, SUM(price) AS merchandise_value,
 SUM(freight_value) AS freight_value, COUNT(*) AS item_count
 FROM olist.order_items GROUP BY order_id
)
SELECT o.order_id, c.customer_state, o.order_status,
 o.order_purchase_timestamp::date AS purchase_date,
 o.order_delivered_customer_date::date AS delivery_date,
 o.order_estimated_delivery_date::date AS estimated_date,
 CASE WHEN o.order_status='delivered' AND o.order_delivered_customer_date IS NOT NULL
 THEN o.order_delivered_customer_date::date > o.order_estimated_delivery_date::date
 END AS is_late,
 CASE WHEN o.order_status='delivered' AND o.order_delivered_customer_date IS NOT NULL
 THEN o.order_delivered_customer_date::date-o.order_purchase_timestamp::date
 END AS delivery_days,
 a.merchandise_value, a.freight_value, a.item_count
FROM olist.orders o JOIN olist.customers c USING(customer_id)
LEFT JOIN amounts a USING(order_id);
