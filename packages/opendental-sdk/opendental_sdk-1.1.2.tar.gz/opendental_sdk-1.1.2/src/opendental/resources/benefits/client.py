"""Benefits client for Open Dental SDK."""

import logging
from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Benefit,
    CreateBenefitRequest,
    UpdateBenefitRequest,
    BenefitListResponse,
    BenefitSearchRequest
)
from .validators import validate_create_benefit_request, validate_update_benefit_request
from .exceptions import BenefitValidationError

logger = logging.getLogger(__name__)


class BenefitsClient(BaseResource):
    """Client for managing benefits in Open Dental."""
    
    def __init__(self, client):
        """Initialize the benefits client."""
        super().__init__(client, "benefits")
    
    def get(self, benefit_id: Union[int, str]) -> Benefit:
        """
        Get a benefit by ID.
        
        Args:
            benefit_id: The benefit ID
            
        Returns:
            Benefit: The benefit object
        """
        benefit_id = self._validate_id(benefit_id)
        endpoint = self._build_endpoint(benefit_id)
        response = self._get(endpoint)
        return self._handle_response(response, Benefit)
    
    def list(self, plan_num: Optional[int] = None, pat_plan_num: Optional[int] = None) -> BenefitListResponse:
        """
        List benefits for a given plan or patient plan.
        
        Args:
            plan_num: Insurance plan number (optional)
            pat_plan_num: Patient plan number (optional)
            
        Returns:
            BenefitListResponse: List of benefits
        """
        params = {}
        if plan_num is not None:
            params["PlanNum"] = plan_num
        if pat_plan_num is not None:
            params["PatPlanNum"] = pat_plan_num
            
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return BenefitListResponse(**response)
        elif isinstance(response, list):
            return BenefitListResponse(
                benefits=[Benefit(**item) for item in response],
                total=len(response),
                page=1,
                per_page=len(response)
            )
        else:
            return BenefitListResponse(benefits=[], total=0, page=1, per_page=0)
    
    def create(self, benefit_data: CreateBenefitRequest) -> Benefit:
        """
        Create a new benefit with pre-validation.
        
        Args:
            benefit_data: The benefit data to create
            
        Returns:
            Benefit: The created benefit object
            
        Raises:
            BenefitValidationError: If validation fails
        """
        # Validate the request before sending to API
        validation_errors = validate_create_benefit_request(benefit_data)
        if validation_errors:
            raise BenefitValidationError(validation_errors)
        
        endpoint = self._build_endpoint()
        data = benefit_data.model_dump(by_alias=True, exclude_none=True)
        
        logger.debug(f"Creating benefit with data: {data}")
        
        try:
            response = self._post(endpoint, json_data=data)
            logger.debug(f"Response type: {type(response)}, Response: {response}")
        except Exception as e:
            logger.error(f"Error creating benefit: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            if hasattr(e, '__traceback__'):
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        # Handle string responses (error case)
        if isinstance(response, str):
            logger.error(f"API returned string response: {response}")
            raise BenefitValidationError(f"API returned error: {response}")
        
        # Handle case where API returns just the ID
        if isinstance(response, dict) and "BenefitNum" in response and len(response) == 1:
            # Create a minimal Benefit object with the returned ID
            try:
                return Benefit(
                    id=response["BenefitNum"],
                    benefit_num=response["BenefitNum"],
                    plan_num=benefit_data.plan_num or 0,
                    benefit_type=benefit_data.benefit_type,
                    monetary_amt=benefit_data.monetary_amt,
                    time_period=benefit_data.time_period,
                    coverage_level=benefit_data.coverage_level,
                    percent=benefit_data.percent or -1,
                    cov_cat_num=benefit_data.cov_cat_num or 0,
                    code_num=benefit_data.code_num or 0,
                    quantity=benefit_data.quantity or 0,
                    code_group_num=benefit_data.code_group_num or 0,
                    quantity_qualifier=benefit_data.quantity_qualifier
                )
            except Exception as e:
                logger.error(f"Error creating Benefit object from ID response: {str(e)}")
                logger.error(f"Response was: {response}")
                raise
        
        try:
            return self._handle_response(response, Benefit)
        except Exception as e:
            logger.error(f"Error in _handle_response: {str(e)}")
            logger.error(f"Response type: {type(response)}, Response: {response}")
            raise
    
    def update(self, benefit_id: Union[int, str], benefit_data: UpdateBenefitRequest) -> Benefit:
        """
        Update an existing benefit with pre-validation.
        
        Args:
            benefit_id: The benefit ID
            benefit_data: The benefit data to update
            
        Returns:
            Benefit: The updated benefit object
            
        Raises:
            BenefitValidationError: If validation fails
        """
        # Validate the request before sending to API
        validation_errors = validate_update_benefit_request(benefit_data)
        if validation_errors:
            raise BenefitValidationError(validation_errors)
        
        benefit_id = self._validate_id(benefit_id)
        endpoint = self._build_endpoint(benefit_id)
        data = benefit_data.model_dump(by_alias=True, exclude_none=True)
        response = self._put(endpoint, json_data=data)
        
        # Handle string responses (error case)
        if isinstance(response, str):
            raise BenefitValidationError(f"API returned error: {response}")
            
        return self._handle_response(response, Benefit)
    
    def delete(self, benefit_id: Union[int, str]) -> bool:
        """
        Delete a benefit.
        
        Args:
            benefit_id: The benefit ID
            
        Returns:
            bool: True if deletion was successful
        """
        benefit_id = self._validate_id(benefit_id)
        endpoint = self._build_endpoint(benefit_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    
    def get_by_plan(self, plan_num: int) -> List[Benefit]:
        """
        Get benefits by plan number.
        
        Args:
            plan_num: Plan number
            
        Returns:
            List[Benefit]: List of benefits for the plan
        """
        result = self.list(plan_num=plan_num)
        return result.benefits
    