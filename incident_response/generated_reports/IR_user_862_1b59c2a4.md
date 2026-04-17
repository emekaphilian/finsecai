# Incident Report: user_862 - txn_4942

**Generated:** 2025-12-04 00:29:43

---

## Alert Summary
- User ID: user_862
- Transaction ID: txn_4942
- Timestamp: NaT
- ML Fraud Score: 0.71
- Rule Hits: 0
- Severity: Medium
- Reason: High model fraud score

## Correlated Events
| txn_id   | user_id   |   amount | merchant_category   |   risk_score |   velocity | timestamp_tx               | ip              | geo   | device_id   |   successful_login | timestamp_auth             |   access_type |   customer_id |   after_hours_flag | timestamp   |   amount_log |   hour |   is_night |   z_score_amount |   is_outlier_z |   txn_count_1h |   merchant_diversity_24h |   iso_outlier |   ml_fraud_score |   rule_hits |   suspicious_sequence |
|:---------|:----------|---------:|:--------------------|-------------:|-----------:|:---------------------------|:----------------|:------|:------------|-------------------:|:---------------------------|--------------:|--------------:|-------------------:|:------------|-------------:|-------:|-----------:|-----------------:|---------------:|---------------:|-------------------------:|--------------:|-----------------:|------------:|----------------------:|
| txn_226  | user_862  |   683.8  | Services            |           94 |          8 | 2025-09-24 19:42:56.371138 | 192.168.145.193 | SG    | Linux       |                  1 | 2025-10-15 22:00:56.304711 |           nan |           nan |                nan | NaT         |      6.52913 |    nan |          0 |         2.41195  |              0 |              0 |                        1 |             0 |            0.145 |           0 |                     0 |
| txn_226  | user_862  |   683.8  | Services            |           94 |          8 | 2025-09-24 19:42:56.371138 | 192.168.59.26   | IN    | Windows     |                  1 | 2025-11-15 21:54:56.305339 |           nan |           nan |                nan | NaT         |      6.52913 |    nan |          0 |         2.41195  |              0 |              0 |                        1 |             0 |            0.145 |           0 |                     0 |
| txn_226  | user_862  |   683.8  | Services            |           94 |          8 | 2025-09-24 19:42:56.371138 | 192.168.41.59   | DE    | Linux       |                  1 | 2025-09-20 22:51:56.314227 |           nan |           nan |                nan | NaT         |      6.52913 |    nan |          0 |         2.41195  |              0 |              0 |                        1 |             0 |            0.145 |           0 |                     0 |
| txn_3203 | user_862  |    64.41 | Retail              |           74 |          3 | 2025-10-14 11:17:56.390545 | 192.168.145.193 | SG    | Linux       |                  1 | 2025-10-15 22:00:56.304711 |           nan |           nan |                nan | NaT         |      4.18068 |    nan |          0 |        -0.691657 |              0 |              0 |                        1 |             0 |            0     |           0 |                     0 |
| txn_3203 | user_862  |    64.41 | Retail              |           74 |          3 | 2025-10-14 11:17:56.390545 | 192.168.59.26   | IN    | Windows     |                  1 | 2025-11-15 21:54:56.305339 |           nan |           nan |                nan | NaT         |      4.18068 |    nan |          0 |        -0.691657 |              0 |              0 |                        1 |             0 |            0     |           0 |                     0 |
| txn_3203 | user_862  |    64.41 | Retail              |           74 |          3 | 2025-10-14 11:17:56.390545 | 192.168.41.59   | DE    | Linux       |                  1 | 2025-09-20 22:51:56.314227 |           nan |           nan |                nan | NaT         |      4.18068 |    nan |          0 |        -0.691657 |              0 |              0 |                        1 |             0 |            0     |           0 |                     0 |
| txn_4942 | user_862  |   754.58 | Services            |           97 |          3 | 2025-10-12 15:07:56.402401 | 192.168.145.193 | SG    | Linux       |                  1 | 2025-10-15 22:00:56.304711 |           nan |           nan |                nan | NaT         |      6.62749 |    nan |          0 |         2.76661  |              0 |              0 |                        1 |             0 |            0.71  |           0 |                     0 |
| txn_4942 | user_862  |   754.58 | Services            |           97 |          3 | 2025-10-12 15:07:56.402401 | 192.168.59.26   | IN    | Windows     |                  1 | 2025-11-15 21:54:56.305339 |           nan |           nan |                nan | NaT         |      6.62749 |    nan |          0 |         2.76661  |              0 |              0 |                        1 |             0 |            0.71  |           0 |                     0 |
| txn_4942 | user_862  |   754.58 | Services            |           97 |          3 | 2025-10-12 15:07:56.402401 | 192.168.41.59   | DE    | Linux       |                  1 | 2025-09-20 22:51:56.314227 |           nan |           nan |                nan | NaT         |      6.62749 |    nan |          0 |         2.76661  |              0 |              0 |                        1 |             0 |            0.71  |           0 |                     0 |
## Recommended Actions
- Monitor user activity closely
- Notify fraud analyst for review
