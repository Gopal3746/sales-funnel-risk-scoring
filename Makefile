.PHONY: setup warehouse train analysis test verify app demo clean

setup:
	python -m pip install -r requirements.txt

warehouse:
	python scripts/build_warehouse.py

train:
	python scripts/train_models.py

analysis:
	python scripts/run_analysis.py

test:
	pytest -q

verify:
	python scripts/verify_project.py

demo: warehouse train analysis verify

app:
	streamlit run dashboard/app.py

clean:
	rm -f warehouse/*.duckdb warehouse/*.wal
	rm -f artifacts/model.joblib artifacts/metrics.json artifacts/feature_names.json
	rm -f artifacts/test_predictions.csv artifacts/open_deal_scores.csv artifacts/shap_top_features.csv artifacts/analysis_summary.csv
