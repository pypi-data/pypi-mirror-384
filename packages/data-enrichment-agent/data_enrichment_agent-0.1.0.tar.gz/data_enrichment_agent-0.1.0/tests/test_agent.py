import pandas as pd
import pytest
from data_enrichment_agent.agent import EnrichmentAgent
from data_enrichment_agent.models import EnrichmentConfig

def create_sample_data():
    df = pd.DataFrame({
        'customer_id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 22, 35, 40],
        'salary': [50000, 60000, 70000, 80000, 90000],
        'department': ['HR', 'IT', 'IT', 'HR', 'IT'],
        'join_date': ['2020-01-15', '2019-03-20', '2021-06-10', '2018-11-05', '2022-02-28']
    })
    # print("create_sample_data", df)
    return df
    
def test_enrichment_agent_end_to_end():
    # Initialize config
    config = EnrichmentConfig(
        model_name="gpt-4.1-mini",
        log_level="ERROR"
    )
    agent = EnrichmentAgent(config=config)
    df = create_sample_data()
    response = agent.enrich_data(
        data=df,
        db_name="test_db",
        schema="public",
        table_name="employee",
        domain_metadata={"industry": "tech"},
        entity_metadata={"entity": "employee"},
        use_case="Predict attrition",
        ml_approach="classification",
        mode="demo",
        sample_rows=3
    )
    # Basic assertions
    assert response.success
    assert response.errors == []
    assert hasattr(response, 'suggestions')
    assert response.suggestions is not None
    assert hasattr(response, 'message')
    # Check that new features were suggested and added
    print("\n\n\n = + = + = + = + End-to-end enrichment workflow test passed. + = + = + = + = \n")
