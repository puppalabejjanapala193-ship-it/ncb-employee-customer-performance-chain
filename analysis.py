import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import seaborn as sns


def regression_metrics(y_true, y_pred):
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    return {"rmse": rmse, "mae": mae, "r2": r2}


def main():
    base_dir = Path(__file__).resolve().parent
    csv_path = base_dir / "NCB_filtered_data_2025-11-26 (2).csv"
    fig_dir = base_dir / "figures"
    fig_dir.mkdir(exist_ok=True)

    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]

    employee_cols = ["ecuso", "equal", "einvol", "etra", "ecomm", "eteam", "eeng", "eitl", "eben"]
    customer_cols = ["cserq", "cbrtel", "cbr", "cbrpb", "ccon"]

    df["employee_index"] = df[employee_cols].mean(axis=1)
    df["customer_index"] = df[customer_cols].mean(axis=1)

    # Size tiers based on terciles
    q1, q2 = df["bsize"].quantile([0.33, 0.66])

    def size_tier(x):
        if x <= q1:
            return "Small"
        if x <= q2:
            return "Medium"
        return "Large"

    df["size_tier"] = df["bsize"].apply(size_tier)

    # Size-tier summary
    key_metrics = ["eeng", "cserq", "cloy", "prod", "teltr"]
    size_summary = (
        df.groupby("size_tier")[key_metrics]
        .mean()
        .reindex(["Small", "Medium", "Large"])
    )
    size_summary.to_csv(fig_dir / "table_size_summary.csv")

    # Correlations
    corr_employee_cserq = float(df["employee_index"].corr(df["cserq"]))
    corr_cserq_cloy = float(df["cserq"].corr(df["cloy"]))
    corr_cloy_prod = float(df["cloy"].corr(df["prod"]))
    corr_teltr_prod = float(df["teltr"].corr(df["prod"]))

    # 1) Employee factors -> service quality (cserq)
    X_cserq = df[employee_cols + ["bsize"]]
    y_cserq = df["cserq"]

    X_train, X_test, y_train, y_test = train_test_split(
        X_cserq, y_cserq, test_size=0.2, random_state=42
    )

    lin_cserq = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LinearRegression())
    ])
    lin_cserq.fit(X_train, y_train)

    pred_cserq_lin = lin_cserq.predict(X_test)
    metrics_cserq_lin = regression_metrics(y_test, pred_cserq_lin)

    rf_cserq = RandomForestRegressor(
        n_estimators=300, random_state=42, min_samples_leaf=2
    )
    rf_cserq.fit(X_train, y_train)

    pred_cserq_rf = rf_cserq.predict(X_test)
    metrics_cserq_rf = regression_metrics(y_test, pred_cserq_rf)

    coef = lin_cserq.named_steps["model"].coef_
    coef_map = dict(zip(X_cserq.columns, coef))
    coef_top = sorted(coef_map.items(), key=lambda x: abs(x[1]), reverse=True)[:5]

    # 2) Service quality -> loyalty (continuous)
    X_cloy = df[["cserq", "cbrtel", "cbr", "cbrpb", "ccon", "employee_index", "bsize"]]
    y_cloy = df["cloy"]

    X_train, X_test, y_train, y_test = train_test_split(
        X_cloy, y_cloy, test_size=0.2, random_state=42
    )

    lin_cloy = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LinearRegression())
    ])
    lin_cloy.fit(X_train, y_train)

    pred = lin_cloy.predict(X_test)
    metrics_cloy_lin = regression_metrics(y_test, pred)

    rf_cloy = RandomForestRegressor(
        n_estimators=300, random_state=42, min_samples_leaf=2
    )
    rf_cloy.fit(X_train, y_train)

    pred_rf = rf_cloy.predict(X_test)
    metrics_cloy_rf = regression_metrics(y_test, pred_rf)

    # 3) Productivity model
    X_prod = df[["cloy", "cserq", "teltr", "bsize", "employee_index"]]
    y_prod = df["prod"]

    X_train, X_test, y_train, y_test = train_test_split(
        X_prod, y_prod, test_size=0.2, random_state=42
    )

    lin_prod = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LinearRegression())
    ])
    lin_prod.fit(X_train, y_train)

    pred_prod_lin = lin_prod.predict(X_test)
    metrics_prod_lin = regression_metrics(y_test, pred_prod_lin)

    rf_prod = RandomForestRegressor(
        n_estimators=300, random_state=42, min_samples_leaf=2
    )
    rf_prod.fit(X_train, y_train)

    pred_prod_rf = rf_prod.predict(X_test)
    metrics_prod_rf = regression_metrics(y_test, pred_prod_rf)

    # Clustering
    cluster_features = df[["employee_index", "customer_index", "prod", "teltr"]].copy()
    scaler = StandardScaler()
    cluster_scaled = scaler.fit_transform(cluster_features)

    best_k = None
    best_sil = -1
    for k in range(2, 6):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(cluster_scaled)
        sil = silhouette_score(cluster_scaled, labels)
        if sil > best_sil:
            best_sil = sil
            best_k = k

    km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels = km.fit_predict(cluster_scaled)
    df["cluster"] = labels

    cluster_summary = (
        df.groupby("cluster")[["employee_index", "customer_index", "prod", "teltr"]]
        .mean()
        .round(3)
    )
    cluster_summary.to_csv(fig_dir / "table_cluster_summary.csv")

    # Figures
    plt.figure(figsize=(10, 8))
    num_cols = employee_cols + customer_cols + ["cloy", "teltr", "prod", "bsize"]
    cor = df[num_cols].corr()
    sns.heatmap(cor, cmap="coolwarm", center=0, square=True)
    plt.title("Correlation Heatmap (Employee, Customer, Performance)")
    plt.tight_layout()
    plt.savefig(fig_dir / "fig1_correlation_heatmap.png", dpi=200)
    plt.close()

    plt.figure(figsize=(6, 4))
    sns.regplot(x="employee_index", y="cserq", data=df, scatter_kws={"alpha": 0.7})
    plt.title("Employee Index vs Service Quality")
    plt.xlabel("Employee Index (avg of survey items)")
    plt.ylabel("Customer Service Quality (cserq)")
    plt.tight_layout()
    plt.savefig(fig_dir / "fig2_employee_vs_service.png", dpi=200)
    plt.close()

    plt.figure(figsize=(6, 4))
    sns.regplot(x="cserq", y="cloy", data=df, scatter_kws={"alpha": 0.7})
    plt.title("Service Quality vs Customer Loyalty")
    plt.xlabel("Customer Service Quality (cserq)")
    plt.ylabel("Customer Loyalty (cloy)")
    plt.tight_layout()
    plt.savefig(fig_dir / "fig3_service_vs_loyalty.png", dpi=200)
    plt.close()

    plt.figure(figsize=(6, 4))
    sns.regplot(x="teltr", y="prod", data=df, scatter_kws={"alpha": 0.7})
    plt.title("Productivity vs Teller Transactions")
    plt.xlabel("Teller Transactions (teltr)")
    plt.ylabel("Productivity (prod)")
    plt.tight_layout()
    plt.savefig(fig_dir / "fig4_prod_vs_teltr.png", dpi=200)
    plt.close()

    plt.figure(figsize=(6, 4))
    sns.boxplot(x="size_tier", y="prod", data=df, order=["Small", "Medium", "Large"])
    plt.title("Productivity by Branch Size Tier")
    plt.xlabel("Branch Size Tier")
    plt.ylabel("Productivity (prod)")
    plt.tight_layout()
    plt.savefig(fig_dir / "fig5_prod_by_size.png", dpi=200)
    plt.close()

    results = {
        "n_branches": int(len(df)),
        "missing_total": int(df.isna().sum().sum()),
        "size_summary": size_summary.round(3).to_dict(),
        "correlations": {
            "employee_index_vs_cserq": round(corr_employee_cserq, 3),
            "cserq_vs_cloy": round(corr_cserq_cloy, 3),
            "cloy_vs_prod": round(corr_cloy_prod, 3),
            "teltr_vs_prod": round(corr_teltr_prod, 3),
        },
        "cserq_models": {
            "linear": {k: round(v, 3) for k, v in metrics_cserq_lin.items()},
            "random_forest": {k: round(v, 3) for k, v in metrics_cserq_rf.items()},
            "top_coefficients": [(k, round(v, 3)) for k, v in coef_top],
        },
        "cloy_models": {
            "linear": {k: round(v, 3) for k, v in metrics_cloy_lin.items()},
            "random_forest": {k: round(v, 3) for k, v in metrics_cloy_rf.items()},
        },
        "prod_models": {
            "linear": {k: round(v, 3) for k, v in metrics_prod_lin.items()},
            "random_forest": {k: round(v, 3) for k, v in metrics_prod_rf.items()},
        },
        "cluster": {
            "best_k": int(best_k),
            "silhouette": round(float(best_sil), 3),
            "sizes": {str(k): int(v) for k, v in df["cluster"].value_counts().sort_index().to_dict().items()},
            "centroids": cluster_summary.round(3).to_dict(),
        },
    }

    with open(fig_dir / "analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
