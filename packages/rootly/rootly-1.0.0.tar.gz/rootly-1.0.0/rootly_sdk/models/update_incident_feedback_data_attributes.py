from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.update_incident_feedback_data_attributes_rating import UpdateIncidentFeedbackDataAttributesRating
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateIncidentFeedbackDataAttributes")


@_attrs_define
class UpdateIncidentFeedbackDataAttributes:
    """
    Attributes:
        feedback (Union[Unset, str]): The feedback of the incident feedback
        rating (Union[Unset, UpdateIncidentFeedbackDataAttributesRating]): The rating of the incident feedback
        anonymous (Union[Unset, bool]): Is the feedback anonymous?
    """

    feedback: Union[Unset, str] = UNSET
    rating: Union[Unset, UpdateIncidentFeedbackDataAttributesRating] = UNSET
    anonymous: Union[Unset, bool] = UNSET

    def to_dict(self) -> dict[str, Any]:
        feedback = self.feedback

        rating: Union[Unset, int] = UNSET
        if not isinstance(self.rating, Unset):
            rating = self.rating.value

        anonymous = self.anonymous

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if feedback is not UNSET:
            field_dict["feedback"] = feedback
        if rating is not UNSET:
            field_dict["rating"] = rating
        if anonymous is not UNSET:
            field_dict["anonymous"] = anonymous

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        feedback = d.pop("feedback", UNSET)

        _rating = d.pop("rating", UNSET)
        rating: Union[Unset, UpdateIncidentFeedbackDataAttributesRating]
        if isinstance(_rating, Unset):
            rating = UNSET
        else:
            rating = UpdateIncidentFeedbackDataAttributesRating(_rating)

        anonymous = d.pop("anonymous", UNSET)

        update_incident_feedback_data_attributes = cls(
            feedback=feedback,
            rating=rating,
            anonymous=anonymous,
        )

        return update_incident_feedback_data_attributes
