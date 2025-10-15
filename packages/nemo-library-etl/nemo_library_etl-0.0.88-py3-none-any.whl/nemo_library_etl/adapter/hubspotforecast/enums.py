from enum import Enum


class HubSpotExtractStep(Enum):
    PIPELINES = "Pipelines"
    DEALS = "Deals"
    DEAL_OWNERS = "DealOwners"
    DEAL_COMPANIES = "DealCompanies"
    COMPANY_DETAILS = "CompanyDetails"
    USERS = "Users"

class HubSpotTransformStep(Enum):
    PLAIN_DEALS = "10_PlainDeals"
    FORECAST = "20_Forecast"
    DEALS_FORECAST_HEADER = "DealsForecastHeader"
    DEALS_FORECAST_DEALS = "DealsForecastDeals"
    