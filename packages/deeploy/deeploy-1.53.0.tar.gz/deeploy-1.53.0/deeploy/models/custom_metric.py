from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict

from deeploy.common.functions import to_lower_camel
from deeploy.enums.graph_type import GraphType


class CustomMetric(BaseModel):
    id: str
    deployment_id: str
    name: str
    graph_type: GraphType
    title_x_axis: str
    title_y_axis: str
    unit_x_axis: Optional[str] = None
    unit_y_axis: Optional[str] = None
    created_at: str
    updated_at: str
    model_config = ConfigDict(alias_generator=to_lower_camel)


class CustomMetricGraphData(CustomMetric):
    average: float
    data: List[float]
    labels: List[Union[float, str]]
    predictionLogIds: Optional[List[List[str]]] = None
    model_config = ConfigDict(alias_generator=to_lower_camel)


class CustomMetricDataPoint(BaseModel):
    id: str
    custom_metric_id: str
    x_value: Union[str, float]
    y_value: float
    predictionLogIds: Optional[List[List[str]]] = None
    created_at: str
    updated_at: str
    model_config = ConfigDict(alias_generator=to_lower_camel)


class CreateCustomMetric(BaseModel):
    """Class that contains the options for create a custom metric"""

    name: str
    """str: name of the custom metric"""
    graph_type: GraphType
    """GraphType, graph type of the custom metric"""
    title_x_axis: str
    """str: title of x axis of the custom metric"""
    title_y_axis: str
    """str: title of y axis of the custom metric"""
    unit_x_axis: Optional[str] = None
    """str, optional: title of x axis of the custom metric"""
    unit_y_axis: Optional[str] = None
    """str, optional: title of y axis of the custom metric"""

    def to_request_body(self) -> Dict:
        request_body = {
            "name": self.name,
            "graphType": self.graph_type.value,
            "titleXAxis": self.title_x_axis,
            "titleYAxis": self.title_y_axis,
            "unitXAxis": self.unit_x_axis,
            "unitYAxis": self.unit_y_axis,
        }
        filtered_request_body = {k: v for k, v in request_body.items() if v is not None and v != {}}
        return filtered_request_body


class UpdateCustomMetric(BaseModel):
    """Class that contains the options for update a custom metric"""

    name: Optional[str] = None
    """str, optional: name of the custom metric"""
    graph_type: Optional[GraphType] = None
    """GraphType, optional, graph type of the custom metric"""
    title_x_axis: Optional[str] = None
    """str, optional: title of x axis of the custom metric"""
    title_y_axis: Optional[str] = None
    """str, optional: title of y axis of the custom metric"""
    unit_x_axis: Optional[str] = None
    """str, optional: title of x axis of the custom metric"""
    unit_y_axis: Optional[str] = None
    """str, optional: title of y axis of the custom metric"""

    def to_request_body(self) -> Dict:
        request_body = {
            "name": self.name,
            "graphType": self.graph_type.value if self.graph_type else None,
            "titleXAxis": self.title_x_axis,
            "titleYAxis": self.title_y_axis,
            "unitXAxis": self.unit_x_axis,
            "unitYAxis": self.unit_y_axis,
        }
        filtered_request_body = {k: v for k, v in request_body.items() if v is not None and v != {}}
        return filtered_request_body


class CreateCustomMetricDataPoint(BaseModel):
    """Class that contains the options for create a custom metric data point"""

    x_value: Union[str, float]
    """str/float: x axis value of data point"""
    y_value: float
    """float: y axis value of data point"""
    prediction_log_ids: Optional[List[str]] = None
    """list: a list of associated prediction log id's for computing metric value"""

    def to_request_body(self) -> Dict:
        request_body = {
            "xValue": self.x_value,
            "yValue": self.y_value,
            "predictionLogIds": self.prediction_log_ids,
        }
        filtered_request_body = {k: v for k, v in request_body.items() if v is not None and v != {}}
        return filtered_request_body
