-- Grain : une ligne par commande ; les articles sont agrégés avant jointure.
-- Retard : date de livraison strictement après la date promise (comparaison par jour).
-- Le taux exclut commandes non livrées et livraisons sans date.
SELECT COUNT(*) AS total_orders,
 COUNT(is_late) AS eligible_deliveries,
 COUNT(*) FILTER (WHERE is_late) AS late_deliveries,
 COUNT(*) FILTER (WHERE order_status='delivered' AND delivery_date IS NULL) AS missing_delivery_dates,
 ROUND(100.0 * COUNT(*) FILTER (WHERE is_late) / NULLIF(COUNT(is_late),0),2) AS late_pct,
 ROUND(AVG(delivery_days),2) AS average_delivery_days,
 PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delivery_days) AS median_delivery_days
FROM olist.delivery_analysis;

SELECT customer_state, COUNT(is_late) AS eligible_deliveries,
 COUNT(*) FILTER (WHERE is_late) AS late_deliveries,
 ROUND(AVG(delivery_days),2) AS average_delivery_days,
 ROUND(100.0 * COUNT(*) FILTER (WHERE is_late) / NULLIF(COUNT(is_late),0),2) AS late_pct
FROM olist.delivery_analysis
GROUP BY customer_state HAVING COUNT(is_late)>=30
ORDER BY late_pct DESC;

-- Valeur des articles des commandes livrées, hors transport, pas un revenu net.
SELECT date_trunc('month',purchase_date)::date AS month,
 SUM(merchandise_value) AS delivered_merchandise_value
FROM olist.delivery_analysis WHERE order_status='delivered'
GROUP BY 1 ORDER BY 1;
