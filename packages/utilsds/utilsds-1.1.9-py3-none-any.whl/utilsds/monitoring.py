import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import pandas as pd
from evidently import ColumnMapping, metrics, tests
from evidently.report import Report
from evidently.test_suite import TestSuite


def mapping(mapping_file: dict[str, list[str]]) -> ColumnMapping:
    """
    Function to create column mapping from configuration file.

    Parameters
    ----------
    mapping_file: dict
        Dictionary containing mapping configuration with possible keys:
        'numerical_features', 'categorical_features', 'datetime', 'id'.

    Returns
    ----------
    ColumnMapping
        Evidently ColumnMapping object with configured mappings.
    """

    column_mapping = ColumnMapping()

    if "numerical_features" in mapping_file:
        column_mapping.numerical_features = mapping_file.get("numerical_features")
    if "categorical_features" in mapping_file:
        column_mapping.categorical_features = mapping_file.get("categorical_features")
    if "datetime" in mapping_file:
        column_mapping.datetime = mapping_file.get("datetime")
    if "id" in mapping_file:
        column_mapping.id = mapping_file.get("id")

    return column_mapping


def test_data(
    current_data: pd.DataFrame,
    reference_data: pd.DataFrame,
    config_file: dict[str, Any],
    stage: str,
) -> pd.DataFrame:
    """
    Function to test data for issues.

    Parameters
    ----------
    current_data: pd.DataFrame
        Current data to test.
    reference_data: pd.DataFrame
        Reference data.
    config_file: dict
        Tests configuration file.
    stage: str
        Stage of the pipeline (either 'test_input' or 'test_output').

    Returns
    ----------
    pd.DataFrame
        Test results.
    """

    column_mapping = mapping(config_file[stage]["mapping"])

    tests_parsed = []

    for test in config_file[stage]["tests"]:
        test_class = getattr(tests, test["type"])
        test_params = test["params"]

        if "column_name" in test_params and isinstance(test_params["column_name"], list):
            columns = test_params["column_name"]
            for column in columns:
                column_test_params = test_params.copy()
                column_test_params["column_name"] = column
                tests_parsed.append(test_class(**column_test_params))
        else:
            tests_parsed.append(test_class(**test_params))

    test_suite = TestSuite(tests=tests_parsed)

    for column in current_data.columns:
        if current_data[column].dtype == "Int64":
            current_data[column] = current_data[column].astype("float64")
    for column in reference_data.columns:
        if reference_data[column].dtype == "Int64":
            reference_data[column] = reference_data[column].astype("float64")

    test_suite.run(current_data=current_data, reference_data=reference_data, column_mapping=column_mapping)
    test_results = test_suite.as_dict()

    test_frame_raw = pd.DataFrame(test_results["tests"])
    test_frame_raw["column"] = test_frame_raw["description"].apply(
        lambda desc: (match.group(1) if (match := re.search(r"\*\*(.*?)\*\*", desc)) is not None else "all columns")
    )

    test_frame_raw["condition"] = test_frame_raw["parameters"].apply(lambda params: params.get("condition", None))
    test_frame_raw["value"] = test_frame_raw["parameters"].apply(lambda params: params.get("value", None))
    test_frame = test_frame_raw[["name", "column", "status", "condition", "value"]].copy()
    test_frame.rename(columns={"name": "test"}, inplace=True)
    test_frame.columns = map(str.upper, test_frame.columns)

    return test_frame


def check_data_drift(
    current_data: pd.DataFrame, reference_data: pd.DataFrame, config_file: dict[str, Any]
) -> pd.DataFrame:
    """
    Function to check data for drift.

    Parameters
    ----------
    current_data: pd.DataFrame
        Current data to check.
    reference_data: pd.DataFrame
        Reference data.
    config_file: dict
        Tests configuration file.

    Returns
    ----------
    pd.DataFrame
        Test results.
    """

    column_mapping = mapping(config_file["drift"]["mapping"])

    metrics_parsed = []

    for metric in config_file["drift"]["metrics"]:
        metric_class = getattr(metrics, metric["type"])
        if "params" in metric:
            metric_params = metric["params"]
            metrics_parsed.append(metric_class(**metric_params))
        else:
            metrics_parsed.append(metric_class())

    report_suite = Report(metrics=metrics_parsed)

    report_suite.run(current_data=current_data, reference_data=reference_data, column_mapping=column_mapping)
    report_suite.save_html("report_html")


def send_email_with_table(
    credentials_frame: pd.DataFrame, subject: str, html_content: str, receiver_email: str
) -> None:
    """
    Function to send email with HTML content.

    Parameters
    ----------
    credentials_frame: pd.DataFrame
        Dataframe with credentials.
    subject: str
        Subject of the email.
    html_content: str
        HTML content to send in the email.
    receiver_email: str
        Email address to send the email to.
    """

    credentials_dict = pd.Series(credentials_frame.setting_value.values, index=credentials_frame.setting_name).to_dict()

    sender_password = credentials_dict.get("MAIL_PASSWORD")
    sender_email = credentials_dict.get("MAIL_SENDER")
    sender_login = credentials_dict.get("MAIL_LOGIN")
    mail_host = credentials_dict.get("MAIL_HOST")
    mail_port = credentials_dict.get("MAIL_PORT")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(mail_host, mail_port, context=context) as server:
        server.login(sender_login, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
