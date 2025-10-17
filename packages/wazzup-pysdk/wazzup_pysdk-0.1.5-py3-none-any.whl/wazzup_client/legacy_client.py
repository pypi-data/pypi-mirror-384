"""Main client that combines tech and public API functionality."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Mapping, Optional, Union

from .tech.client import WazzupTechClient
from .public.client import WazzupPublicClient
from .tech.schemas import AccountCreate, TechUser
from .public.schemas import User, IFrameRequest


class WazzupLegacyClient:
    """Main client that combines tech and public API functionality."""
    
    def __init__(
        self,
        api_key: str,
        tech_base_url: str = "https://tech.wazzup24.com",
        public_base_url: str = "https://api.wazzup24.com",
        *,
        timeout: Optional[float] = None,
    ) -> None:
        """Initialize the Wazzup client.
        
        Args:
            api_key: API key (client API key for most operations, partner API key for account creation)
            tech_base_url: Base URL for tech API
            public_base_url: Base URL for public API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.tech_base_url = tech_base_url
        self.public_base_url = public_base_url
        
        # Initialize both clients with the same API key
        self._tech_client = WazzupTechClient(
            base_url=tech_base_url,
            api_key=api_key,
            timeout=timeout
        )
        
        self._public_client = WazzupPublicClient(
            base_url=public_base_url,
            api_key=api_key,
            timeout=timeout
        )
    
    async def create_account(
        self,
        name: str,
        lang: str = "en",
        currency: str = "USD",
        crm_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new account and return account details with client API key.
        
        Note: This requires a partner API key. If you're using a client API key,
        this will raise an error from the API.
        
        Args:
            name: Account name
            lang: Language code (ru, en, es, pt)
            currency: Currency code (RUR, EUR, USD, KZT)
            crm_key: CRM key (will be generated if not provided)
            
        Returns:
            Dictionary containing accountId, apiKey, and other account details
        """
        if not crm_key:
            import uuid
            crm_key = f"crm_{uuid.uuid4().hex[:16]}"
        
        account_data = AccountCreate(
            crmKey=crm_key,
            name=name,
            lang=lang,
            currency=currency
        )
        
        return await self._tech_client.create_account(account_data)
    
    # Account Management (Tech API)
    async def get_account_settings(self) -> Dict[str, Any]:
        """Get account settings.
        
        Returns:
            Account settings including pushInputOutputMessageEventsForManagers and userRoles
        """
        return await self._tech_client.get_settings()
    
    async def update_account_settings(
        self,
        push_input_output_message_events_for_managers: Optional[bool] = None,
        user_roles: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Update account settings with automatic preservation of existing values.
        
        Args:
            push_input_output_message_events_for_managers: Whether to notify managers about new messages
            user_roles: List of user roles to set (if None, preserves existing)
            
        Returns:
            Updated settings
        """
        # Get current settings to preserve existing values
        current_settings = await self.get_account_settings()
        
        # Update only the fields that were provided
        if push_input_output_message_events_for_managers is not None:
            current_settings["pushInputOutputMessageEventsForManagers"] = push_input_output_message_events_for_managers
        
        if user_roles is not None:
            current_settings["userRoles"] = user_roles
        
        return await self._tech_client.patch_settings(current_settings)
    
    async def assign_user_to_channel(
        self,
        user_id: str,
        channel_id: str,
        role: str = "seller",
        allow_get_new_clients: bool = True
    ) -> Dict[str, Any]:
        """Assign a user to a channel with specific role and permissions.
        
        Args:
            user_id: User ID to assign
            channel_id: Channel ID (UUID string)
            role: User role - "auditor" (quality control), "seller" (manager), or "manager" (supervisor)
            allow_get_new_clients: Whether user can receive new clients
            
        Returns:
            Updated settings with the new user role assignment
        """
        # Get current settings to preserve existing user roles
        current_settings = await self.get_account_settings()
        current_user_roles = current_settings.get("userRoles", [])
        
        # Create new user role item
        new_user_role = {
            "channelId": channel_id,
            "userId": user_id,
            "role": role,
            "allowGetNewClients": allow_get_new_clients
        }
        
        # Remove any existing role for this user on this channel
        current_user_roles = [
            role_item for role_item in current_user_roles 
            if not (role_item.get("userId") == user_id and role_item.get("channelId") == channel_id)
        ]
        
        # Add the new role
        current_user_roles.append(new_user_role)
        
        # Update settings with the new user roles
        result = await self.update_account_settings(user_roles=current_user_roles)
        return {"success": True, "message": f"User {user_id} assigned to channel as {role}", "settings": result}
    
    async def assign_users_to_channel(
        self,
        user_assignments: List[Dict[str, Any]],
        channel_id: str
    ) -> Dict[str, Any]:
        """Assign multiple users to a channel with different roles and permissions.
        
        Args:
            user_assignments: List of user assignment dictionaries, each containing:
                - user_id: User ID to assign
                - role: User role - "auditor", "seller", or "manager"
                - allow_get_new_clients: Whether user can receive new clients (optional, defaults to True)
            channel_id: Channel ID (UUID string)
            
        Returns:
            Updated settings with the new user role assignments
        """
        # Get current settings to preserve existing user roles
        current_settings = await self.get_account_settings()
        current_user_roles = current_settings.get("userRoles", [])
        
        # Remove any existing roles for these users on this channel
        assigned_user_ids = [assignment["user_id"] for assignment in user_assignments]
        current_user_roles = [
            role_item for role_item in current_user_roles 
            if not (role_item.get("userId") in assigned_user_ids and role_item.get("channelId") == channel_id)
        ]
        
        # Add the new roles
        for assignment in user_assignments:
            new_user_role = {
                "channelId": channel_id,
                "userId": assignment["user_id"],
                "role": assignment["role"],
                "allowGetNewClients": assignment.get("allow_get_new_clients", True)
            }
            current_user_roles.append(new_user_role)
        
        # Update settings with the new user roles
        result = await self.update_account_settings(user_roles=current_user_roles)
        return {"success": True, "message": f"{len(user_assignments)} users assigned to channel", "settings": result}
    
    async def remove_user_from_channel(self, user_id: str, channel_id: str) -> Dict[str, Any]:
        """Remove a user's access to a specific channel.
        
        Args:
            user_id: User ID to remove
            channel_id: Channel ID (UUID string)
            
        Returns:
            Updated settings with the user role removed
        """
        # Get current settings
        current_settings = await self.get_account_settings()
        current_user_roles = current_settings.get("userRoles", [])
        
        # Remove the user role for this channel
        updated_user_roles = [
            role_item for role_item in current_user_roles 
            if not (role_item.get("userId") == user_id and role_item.get("channelId") == channel_id)
        ]
        
        # Update settings
        result = await self.update_account_settings(user_roles=updated_user_roles)
        return {"success": True, "message": f"User {user_id} removed from channel", "settings": result}

    async def get_webhook_settings(self) -> Dict[str, Any]:
        """Fetch the current webhook configuration for the account."""
        return await self._public_client.get_webhooks_settings()

    async def update_webhook_settings(self, settings: Mapping[str, Any]) -> Dict[str, Any]:
        """Update webhook configuration."""
        return await self._public_client.patch_webhooks(settings)

    async def test_webhook(self, uri: str) -> Dict[str, Any]:
        """Trigger a test webhook call towards the provided URI."""
        return await self._tech_client.send_test_webhook(uri)
    
    async def get_user_channel_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all channel roles for a specific user.
        
        Args:
            user_id: User ID to check
            
        Returns:
            List of channel roles for the user
        """
        current_settings = await self.get_account_settings()
        user_roles = current_settings.get("userRoles", [])
        
        return [
            role_item for role_item in user_roles 
            if role_item.get("userId") == user_id
        ]
    
    async def list_channels(self) -> List[Dict[str, Any]]:
        """List all channels for the account.
        
        Returns:
            List of channel information
        """
        channels = await self._public_client.get_channels()
        
        # If channels is empty, try to initialize session by calling get_account_settings
        # This is a workaround for the API's lazy initialization behavior
        if not channels:
            try:
                await self.get_account_settings()
                # Retry the channels call after session initialization
                channels = await self._public_client.get_channels()
            except Exception:
                # If session initialization fails, return the original empty result
                pass
        
        return channels
    
    async def get_channel_info(self, transport: str, channel_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific channel.
        
        Args:
            transport: Channel transport type
            channel_id: Channel ID
            
        Returns:
            Channel information
        """
        return await self._tech_client.get_channel_info(transport, channel_id)
    
    async def create_channel(self, transport: str, **kwargs) -> Dict[str, Any]:
        """Create a new channel.
        
        Args:
            transport: Channel transport type
            **kwargs: Additional channel parameters
            
        Returns:
            Channel creation result
        """
        return await self._tech_client.create_channel(transport, kwargs or None)

    async def reinit_channel(self, transport: str, channel_id: str) -> Dict[str, Any]:
        """Reinitialize an existing channel session."""
        return await self._tech_client.reinit_channel(transport, channel_id)

    async def generate_channel_link(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Generate a link for connecting channels via iframe flow."""
        return await self._tech_client.generate_channel_link(payload)
    
    async def delete_channel(self, transport: str, channel_id: str, delete_chats: bool = True) -> Dict[str, Any]:
        """Delete a channel.
        
        Args:
            transport: Channel transport type
            channel_id: Channel ID
            delete_chats: Whether to delete associated chats
            
        Returns:
            Deletion result
        """
        return await self._tech_client.delete_channel(transport, channel_id, delete_chats)
    
    # User Management (Public API)
    async def list_users(self) -> List[Dict[str, Any]]:
        """List all users in the account.
        
        Returns:
            List of user information
        """
        return await self._public_client.get_users()
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            User information
        """
        return await self._public_client.get_user(user_id)
    
    async def create_user(
        self,
        user_id: str,
        name: str,
        phone: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new user in the account.
        
        Args:
            user_id: Unique user ID (up to 64 characters)
            name: User name (up to 150 characters)
            phone: Phone number in international format (e.g., 79261234567)
            **kwargs: Additional user parameters
            
        Returns:
            User creation result (may be empty dict if successful)
        """
        user_data = {
            "id": user_id,
            "name": name,
            **kwargs
        }
        
        if phone:
            user_data["phone"] = phone
        
        try:
            result = await self._public_client.post_users([user_data])
            # The API returns empty response on success, so return a success indicator
            return result if result else {"success": True, "message": "User created successfully"}
        except Exception as e:
            # Handle JSON decode errors (empty response)
            if "Expecting value" in str(e):
                return {"success": True, "message": "User created successfully"}
            raise
    
    async def create_users(self, users_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple users in the account (up to 100 per request).
        
        Args:
            users_data: List of user data dictionaries, each containing:
                - id: Unique user ID (up to 64 characters)
                - name: User name (up to 150 characters)  
                - phone: Phone number in international format (optional)
                
        Returns:
            User creation result
            
        Raises:
            ValueError: If more than 100 users provided
        """
        if len(users_data) > 100:
            raise ValueError("Cannot create more than 100 users in a single request")
        
        try:
            result = await self._public_client.post_users(users_data)
            return result if result else {"success": True, "message": f"{len(users_data)} users created successfully"}
        except Exception as e:
            # Handle JSON decode errors (empty response)
            if "Expecting value" in str(e):
                return {"success": True, "message": f"{len(users_data)} users created successfully"}
            raise
    
    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user from the account.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            Deletion result (may be empty dict if successful)
        """
        try:
            result = await self._public_client.delete_user(user_id)
            return result if result else {"success": True, "message": "User deleted successfully"}
        except Exception as e:
            # Handle JSON decode errors (empty response)
            if "Expecting value" in str(e):
                return {"success": True, "message": "User deleted successfully"}
            raise
    
    async def bulk_delete_users(self, user_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple users from the account in a single request.
        
        Args:
            user_ids: List of user IDs to delete
            
        Returns:
            Deletion result with information about which users were deleted
            and which were not found (if any)
        """
        try:
            result = await self._public_client.bulk_delete_users(user_ids)
            # The API returns empty array on success, or array of IDs that were not found
            if result == []:
                return {"success": True, "message": f"{len(user_ids)} users deleted successfully", "deleted": user_ids}
            else:
                # Some users were not found
                not_found = result
                deleted = [uid for uid in user_ids if uid not in not_found]
                return {
                    "success": True, 
                    "message": f"{len(deleted)} users deleted successfully, {len(not_found)} users not found",
                    "deleted": deleted,
                    "not_found": not_found
                }
        except Exception as e:
            # Handle JSON decode errors (empty response)
            if "Expecting value" in str(e):
                return {"success": True, "message": f"{len(user_ids)} users deleted successfully", "deleted": user_ids}
            raise
    
    # Contact Management (Public API)
    async def list_contacts(self, offset: int = 0) -> Dict[str, Any]:
        """List contacts in the account.
        
        Args:
            offset: Pagination offset
            
        Returns:
            Dictionary containing count and data array of contacts
        """
        return await self._public_client.get_contacts(offset)
    
    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific contact.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            Contact information
        """
        return await self._public_client.get_contact(contact_id)
    
    async def create_contact(
        self,
        contact_id: str,
        responsible_user_id: str,
        name: str,
        contact_data: List[Dict[str, Any]],
        uri: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new contact.
        
        Args:
            contact_id: ID of the contact in CRM system (max 100 characters)
            responsible_user_id: ID of the responsible user (max 100 characters)
            name: Contact name (max 200 characters)
            contact_data: List of contact data objects with chatType, chatId, etc.
            uri: Optional link to contact in CRM (max 200 characters)
            
        Returns:
            Contact creation result
        """
        contact_payload = {
            "id": contact_id,
            "responsibleUserId": responsible_user_id,
            "name": name,
            "contactData": contact_data
        }
        if uri:
            contact_payload["uri"] = uri
        
        try:
            result = await self._public_client.create_contact(contact_payload)
            return result if result else {"success": True, "message": "Contact created successfully"}
        except Exception as e:
            if "Expecting value" in str(e):
                return {"success": True, "message": "Contact created successfully"}
            raise
    
    async def create_contacts(self, contacts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple contacts in the account (up to 100 per request).
        
        Args:
            contacts_data: List of contact data dictionaries, each containing:
                - id: Contact ID in CRM system (max 100 characters)
                - responsibleUserId: ID of responsible user (max 100 characters)
                - name: Contact name (max 200 characters)
                - contactData: List of contact data objects
                - uri: Optional link to contact in CRM (max 200 characters)
                
        Returns:
            Contact creation result
            
        Raises:
            ValueError: If more than 100 contacts provided
        """
        if len(contacts_data) > 100:
            raise ValueError("Cannot create more than 100 contacts in a single request")
        
        try:
            result = await self._public_client.create_contacts(contacts_data)
            return result if result else {"success": True, "message": f"{len(contacts_data)} contacts created successfully"}
        except Exception as e:
            if "Expecting value" in str(e):
                return {"success": True, "message": f"{len(contacts_data)} contacts created successfully"}
            raise
    
    async def update_contact(
        self,
        contact_id: str,
        responsible_user_id: str,
        name: str,
        contact_data: List[Dict[str, Any]],
        uri: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing contact.
        
        Note: This uses the same endpoint as create_contact since the API
        creates or updates based on the contact ID.
        
        Args:
            contact_id: ID of the contact in CRM system (max 100 characters)
            responsible_user_id: ID of the responsible user (max 100 characters)
            name: Contact name (max 200 characters)
            contact_data: List of contact data objects with chatType, chatId, etc.
            uri: Optional link to contact in CRM (max 200 characters)
            
        Returns:
            Contact update result
        """
        return await self.create_contact(contact_id, responsible_user_id, name, contact_data, uri)
    
    async def delete_contact(self, contact_id: str) -> Dict[str, Any]:
        """Delete a contact from the account.
        
        Args:
            contact_id: Contact ID to delete
            
        Returns:
            Deletion result (may be empty dict if successful)
        """
        try:
            result = await self._public_client.delete_contact(contact_id)
            return result if result else {"success": True, "message": "Contact deleted successfully"}
        except Exception as e:
            if "Expecting value" in str(e):
                return {"success": True, "message": "Contact deleted successfully"}
            raise
    
    async def bulk_delete_contacts(self, contact_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple contacts from the account in a single request.
        
        Args:
            contact_ids: List of contact IDs to delete
            
        Returns:
            Deletion result with information about which contacts were deleted
            and which were not found (if any)
        """
        try:
            result = await self._public_client.bulk_delete_contacts(contact_ids)
            # The API returns empty array on success, or array of IDs that were not found
            if result == []:
                return {"success": True, "message": f"{len(contact_ids)} contacts deleted successfully", "deleted": contact_ids}
            else:
                # Some contacts were not found
                not_found = result
                deleted = [cid for cid in contact_ids if cid not in not_found]
                return {
                    "success": True, 
                    "message": f"{len(deleted)} contacts deleted successfully, {len(not_found)} contacts not found",
                    "deleted": deleted,
                    "not_found": not_found
                }
        except Exception as e:
            if "Expecting value" in str(e):
                return {"success": True, "message": f"{len(contact_ids)} contacts deleted successfully", "deleted": contact_ids}
            raise
    
    # Deal Management (Public API)
    async def list_deals(self, offset: int = 0) -> Dict[str, Any]:
        """List deals in the account.
        
        Args:
            offset: Pagination offset
            
        Returns:
            Dictionary containing count and data array of deals
        """
        return await self._public_client.get_deals(offset)
    
    async def get_deal(self, deal_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific deal.
        
        Args:
            deal_id: Deal ID
            
        Returns:
            Deal information
        """
        return await self._public_client.get_deal(deal_id)
    
    async def create_deal(
        self,
        deal_id: str,
        responsible_user_id: str,
        name: str,
        contacts: List[str],
        uri: str,
        closed: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Create a new deal.
        
        Args:
            deal_id: ID of the deal in CRM system (max 100 characters)
            responsible_user_id: ID of the responsible user (max 100 characters)
            name: Deal name (max 200 characters)
            contacts: List of contact IDs associated with the deal (1-10 contacts)
            uri: Link to deal in CRM (max 200 characters)
            closed: Optional flag indicating if deal is closed
            
        Returns:
            Deal creation result
        """
        deal_payload = {
            "id": deal_id,
            "responsibleUserId": responsible_user_id,
            "name": name,
            "contacts": contacts,
            "uri": uri
        }
        if closed is not None:
            deal_payload["closed"] = closed
        
        try:
            result = await self._public_client.post_deals([deal_payload])
            return result if result else {"success": True, "message": "Deal created successfully"}
        except Exception as e:
            if "Expecting value" in str(e):
                return {"success": True, "message": "Deal created successfully"}
            raise
    
    async def create_deals(self, deals_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple deals in the account (up to 100 per request).
        
        Args:
            deals_data: List of deal data dictionaries, each containing:
                - id: Deal ID in CRM system (max 100 characters)
                - responsibleUserId: ID of responsible user (max 100 characters)
                - name: Deal name (max 200 characters)
                - contacts: List of contact IDs (1-10 contacts)
                - uri: Link to deal in CRM (max 200 characters)
                - closed: Optional flag indicating if deal is closed
                
        Returns:
            Deal creation result
            
        Raises:
            ValueError: If more than 100 deals provided
        """
        if len(deals_data) > 100:
            raise ValueError("Cannot create more than 100 deals in a single request")
        
        try:
            result = await self._public_client.post_deals(deals_data)
            return result if result else {"success": True, "message": f"{len(deals_data)} deals created successfully"}
        except Exception as e:
            if "Expecting value" in str(e):
                return {"success": True, "message": f"{len(deals_data)} deals created successfully"}
            raise
    
    async def update_deal(
        self,
        deal_id: str,
        responsible_user_id: str,
        name: str,
        contacts: List[str],
        uri: str,
        closed: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update an existing deal.
        
        Note: This uses the same endpoint as create_deal since the API
        creates or updates based on the deal ID.
        
        Args:
            deal_id: ID of the deal in CRM system (max 100 characters)
            responsible_user_id: ID of the responsible user (max 100 characters)
            name: Deal name (max 200 characters)
            contacts: List of contact IDs associated with the deal (1-10 contacts)
            uri: Link to deal in CRM (max 200 characters)
            closed: Optional flag indicating if deal is closed
            
        Returns:
            Deal update result
        """
        return await self.create_deal(deal_id, responsible_user_id, name, contacts, uri, closed)
    
    async def delete_deal(self, deal_id: str) -> Dict[str, Any]:
        """Delete a deal from the account.
        
        Args:
            deal_id: Deal ID to delete
            
        Returns:
            Deletion result (may be empty dict if successful)
        """
        try:
            result = await self._public_client.delete_deal(deal_id)
            return result if result else {"success": True, "message": "Deal deleted successfully"}
        except Exception as e:
            if "Expecting value" in str(e):
                return {"success": True, "message": "Deal deleted successfully"}
            raise
    
    async def bulk_delete_deals(self, deal_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple deals from the account in a single request.
        
        Args:
            deal_ids: List of deal IDs to delete
            
        Returns:
            Deletion result with information about which deals were deleted
            and which were not found (if any)
        """
        try:
            result = await self._public_client.bulk_delete_deals(deal_ids)
            # The API returns empty array on success, or array of IDs that were not found
            if result == []:
                return {"success": True, "message": f"{len(deal_ids)} deals deleted successfully", "deleted": deal_ids}
            else:
                # Some deals were not found
                not_found = result
                deleted = [did for did in deal_ids if did not in not_found]
                return {
                    "success": True, 
                    "message": f"{len(deleted)} deals deleted successfully, {len(not_found)} deals not found",
                    "deleted": deleted,
                    "not_found": not_found
                }
        except Exception as e:
            if "Expecting value" in str(e):
                return {"success": True, "message": f"{len(deal_ids)} deals deleted successfully", "deleted": deal_ids}
            raise
    
    # Pipeline Management (Public API)
    async def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all pipelines (sales funnels) in the account.
        
        Returns:
            List of pipeline information with stages
        """
        return await self._public_client.get_pipelines()
    
    async def create_pipeline(
        self,
        pipeline_id: str,
        name: str,
        stages: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Create a new pipeline (sales funnel).
        
        Args:
            pipeline_id: ID of the pipeline in CRM system (max 100 characters)
            name: Pipeline name (max 100 characters)
            stages: Optional list of stage dictionaries, each containing:
                - id: Stage ID (max 100 characters)
                - name: Stage name (max 100 characters)
                
        Returns:
            Pipeline creation result
        """
        pipeline_payload = {
            "id": pipeline_id,
            "name": name
        }
        if stages:
            pipeline_payload["stages"] = stages
        
        try:
            result = await self._public_client.post_pipelines([pipeline_payload])
            return result if result else {"success": True, "message": "Pipeline created successfully"}
        except Exception as e:
            if "Expecting value" in str(e):
                return {"success": True, "message": "Pipeline created successfully"}
            raise
    
    async def create_pipelines(self, pipelines_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple pipelines in the account.
        
        Args:
            pipelines_data: List of pipeline data dictionaries, each containing:
                - id: Pipeline ID in CRM system (max 100 characters)
                - name: Pipeline name (max 100 characters)
                - stages: Optional list of stage dictionaries
                
        Returns:
            Pipeline creation result
        """
        try:
            result = await self._public_client.post_pipelines(pipelines_data)
            return result if result else {"success": True, "message": f"{len(pipelines_data)} pipelines created successfully"}
        except Exception as e:
            if "Expecting value" in str(e):
                return {"success": True, "message": f"{len(pipelines_data)} pipelines created successfully"}
            raise
    
    async def update_pipeline(
        self,
        pipeline_id: str,
        name: str,
        stages: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Update an existing pipeline.
        
        Note: This uses the same endpoint as create_pipeline since the API
        creates or updates based on the pipeline ID.
        
        Args:
            pipeline_id: ID of the pipeline in CRM system (max 100 characters)
            name: Pipeline name (max 100 characters)
            stages: Optional list of stage dictionaries, each containing:
                - id: Stage ID (max 100 characters)
                - name: Stage name (max 100 characters)
                
        Returns:
            Pipeline update result
        """
        return await self.create_pipeline(pipeline_id, name, stages)
    
    # Balance and Transactions (Tech API)
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance.
        
        Returns:
            Balance information
        """
        return await self._tech_client.get_balance()
    
    async def increase_balance(self, account_id: int, value: int) -> Dict[str, Any]:
        """Increase account balance.
        Requires partner API key.
        Args:
            account_id: ID of the child account
            value: Amount in child account currency to increase the limit
            
        Returns:
            Balance update result
        """
        return await self._tech_client.increase_balance({"accountId": account_id, "value": value})
    
    # iFrame Management (Public API)
    async def generate_iframe_link(
        self,
        user_id: str,
        user_name: str,
        scope: str = "global",
        filters: Optional[List[Dict[str, Any]]] = None,
        active_chat: Optional[Dict[str, Any]] = None,
        use_deals_events: Optional[bool] = None,
        use_message_events: Optional[bool] = None,
        client_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate iframe link for chat window.
        
        Args:
            user_id: ID of the user in CRM who opens the chat window
            user_name: Name of the user (will be used as sender name)
            scope: Context for opening the window - "global" for all chats, "card" for specific chat
            filters: List of chat filters (required when scope="card")
            active_chat: Chat to open as active (optional)
            use_deals_events: Enable deal events from iframe
            use_message_events: Enable message events from iframe
            client_type: Type of CRM (optional)
            
        Returns:
            Dictionary containing the iframe URL
            
        Raises:
            ValueError: If scope is "card" but no filters provided
        """
        if scope == "card" and not filters:
            raise ValueError("filters are required when scope is 'card'")
        
        # Build the request data
        request_data = {
            "user": {
                "id": user_id,
                "name": user_name
            },
            "scope": scope
        }
        
        if filters:
            request_data["filter"] = filters
        
        if active_chat:
            request_data["activeChat"] = active_chat
        
        # Build options if any event settings are provided
        options = {}
        if use_deals_events is not None:
            options["useDealsEvents"] = use_deals_events
        if use_message_events is not None:
            options["useMessageEvents"] = use_message_events
        if client_type:
            options["clientType"] = client_type
        
        if options:
            request_data["options"] = options
        
        return await self._public_client.generate_iframe_link(request_data)
    
    # Utility Methods
    async def close(self) -> None:
        """Close all client connections."""
        await self._tech_client.close()
        await self._public_client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
