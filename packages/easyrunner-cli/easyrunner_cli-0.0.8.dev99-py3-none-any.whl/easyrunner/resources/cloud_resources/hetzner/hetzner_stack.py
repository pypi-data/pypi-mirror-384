from typing import Any, Optional

import pulumi
import pulumi.automation as auto
from pulumi.automation import UpdateSummary

from ....types.exec_result import ExecResult
from ..cloud_resource_pulumi_base import CloudProviderBase
from .hetzner_virtual_machine import HetznerVirtualMachine


class Stack:
    """Base class for managing cloud stacks."""

    def __init__(self, stack_name: str, provider: CloudProviderBase, backend_url: Optional[str] = None) -> None:
        self.provider = provider
        self.stack_name = stack_name
        self.backend_url = backend_url

    def _convert_pulumi_outputs_to_dict(self, outputs: auto.OutputMap) -> dict[str, Any]:
        """Convert Pulumi OutputMap to standard dict."""
        return {k: v.value for k, v in outputs.items()}

    def _create_vm_program(self, vm_config: HetznerVirtualMachine) -> None:
        """Pulumi program to create VM resources."""
        import pulumi_hcloud as hetzner

        # Get the provider instance
        provider_instance = self.provider.get_provider_instance()

        firewalls = []

        # Create firewall rules if provided
        if vm_config.firewalls:
            for fw in vm_config.firewalls:

                # Convert FirewallRuleConfig to Pulumi format
                firewall_rules = []
                for rule in fw.rules:
                    rule_dict = {
                        "direction": rule.direction,
                        "protocol": rule.protocol,
                        "source_ips": rule.source_ips,
                    }

                    # Add optional fields if they exist
                    if hasattr(rule, 'port') and rule.port is not None:
                        rule_dict["port"] = rule.port

                    if hasattr(rule, 'destination_ips') and rule.destination_ips:
                        rule_dict["destination_ips"] = rule.destination_ips

                    firewall_rules.append(rule_dict)

                # Create the firewall
                firewalls.append(hetzner.Firewall(
                    resource_name=f"{vm_config.name}-{fw.name}",
                    labels=fw.labels or {},
                    rules=firewall_rules,
                    opts=pulumi.ResourceOptions(provider=provider_instance),
                ))

        # Create SSH key if provided
        ssh_key = None
        if vm_config.ssh_keys:
            ssh_key = hetzner.SshKey(
                resource_name=f"{vm_config.name}-key",
                public_key=vm_config.ssh_keys[0],  # Use first key
                opts=pulumi.ResourceOptions(provider=provider_instance),
            )

        # Create server
        server_args = {
            "image": vm_config.image,
            "server_type": vm_config.size,
            "location": vm_config.location or self.provider.region,
            "ssh_keys": [ssh_key.id] if ssh_key else [],
            "labels": vm_config.labels,
        }

        # Add firewall IDs if provided
        if firewalls:
            server_args["firewall_ids"] = [fw.id for fw in firewalls]

        server = hetzner.Server(
            resource_name=vm_config.name,
            **server_args,
            opts=pulumi.ResourceOptions(provider=provider_instance),
        )

        # Export outputs properly - ensure they're resolved as native types
        pulumi.export("server_id", server.id.apply(lambda x: str(x)))
        pulumi.export("server_ip", server.ipv4_address.apply(lambda x: str(x)))

    def create_or_select_stack(
        self, vm_config: HetznerVirtualMachine
    ) -> auto.Stack:
        """Create or select a Pulumi stack."""
        # Create a closure that captures vm_config
        def program() -> None:
            self._create_vm_program(vm_config)

        return auto.create_or_select_stack(
            stack_name=self.stack_name,
            project_name=self.provider.project_name,
            program=program,
            opts=self.provider._create_workspace_options(backend_url=self.backend_url),
        )

    def select_stack(self) -> Optional[auto.Stack]:
        """Select an existing Pulumi stack."""
        try:
            return auto.select_stack(
                stack_name=self.stack_name,
                project_name=self.provider.project_name,
                program=lambda: None,  # Empty program for selection
                opts=self.provider._create_workspace_options(
                    backend_url=self.backend_url
                ),
            )
        except auto.StackNotFoundError:
            return None

    def cancel(self) -> ExecResult[None]:
        """Cancel any currently running operation on the stack and unlock it.

        This is useful when a stack is locked due to a previous operation that didn't complete properly.

        Returns:
            ExecResult indicating success/failure of the cancellation
        """
        try:
            stack = self.select_stack()
            if not stack:
                return ExecResult(
                    success=False,
                    return_code=1,
                    stdout="",
                    stderr=f"Stack '{self.stack_name}' not found",
                )

            # Cancel the current operation
            stack.cancel()

            return ExecResult(
                success=True,
                return_code=0,
                stdout=f"Stack '{self.stack_name}' cancelled and unlocked successfully",
                stderr="",
            )
        except auto.StackNotFoundError:
            return ExecResult(
                success=False,
                return_code=1,
                stdout="",
                stderr=f"Stack '{self.stack_name}' does not exist",
            )
        except Exception as e:
            error_msg = f"Failed to cancel stack '{self.stack_name}': {str(e)}"
            return ExecResult(success=False, return_code=1, stdout="", stderr=error_msg)

    def refresh(self) -> ExecResult[None]:
        """Refresh the stack state to match the actual cloud provider state.
        
        This syncs Pulumi's state with what actually exists in the cloud provider,
        which is useful when:
        - Resources were manually deleted outside of Pulumi
        - Previous operations were interrupted
        - The state is out of sync with reality
        
        Returns:
            ExecResult indicating success/failure of the refresh
        """
        try:
            stack = self.select_stack()
            if not stack:
                return ExecResult(
                    success=False,
                    return_code=1,
                    stdout="",
                    stderr=f"Stack '{self.stack_name}' not found",
                )

            # Refresh the stack state
            result = stack.refresh()
            
            return ExecResult(
                success=True if result.summary.result == "succeeded" else False,
                return_code=0 if result.summary.result == "succeeded" else 1,
                stdout=result.stdout if hasattr(result, 'stdout') else f"Stack '{self.stack_name}' refreshed successfully",
                stderr=result.stderr if hasattr(result, 'stderr') else "",
            )
        except auto.StackNotFoundError:
            return ExecResult(
                success=False,
                return_code=1,
                stdout="",
                stderr=f"Stack '{self.stack_name}' does not exist",
            )
        except Exception as e:
            error_msg = f"Failed to refresh stack '{self.stack_name}': {str(e)}"
            return ExecResult(success=False, return_code=1, stdout="", stderr=error_msg)

    def destroy(self) -> ExecResult[UpdateSummary]:
        """Destroy deletes all resources in a stack, leaving all history and configuration intact.

        If you want to permanently remove the stack by cleaning up state, use the remove() method after this.
        
        This method handles common edge cases:
        - If resources are already deleted in the cloud provider, it refreshes the state first
        - If there are pending operations from interrupted previous runs, it attempts to recover
        """
        stack = self.select_stack()
        if not stack:
            return ExecResult(
                success=False,
                return_code=1,
                stdout="",
                stderr=f"Stack '{self.stack_name}' not found",
            )
        
        try:
            result = stack.destroy()
            exec_result = ExecResult(
                success=True if result.summary.result == "succeeded" else False,
                return_code=0 if result.summary.result == "succeeded" else 1,
                stdout=result.stdout,
                stderr=result.stderr,
            )
            exec_result.result = result.summary
            return exec_result
        except Exception as e:
            error_msg = str(e)
            
            # Check if this is a "resource not found" or "pending operations" error
            # These indicate the state is out of sync with reality
            should_refresh = any(indicator in error_msg.lower() for indicator in [
                "not found",
                "pending operations",
                "interrupted while",
                "unknown state"
            ])
            
            if should_refresh:
                # Try to refresh the state to sync with actual cloud provider state
                refresh_result = self.refresh()
                
                if refresh_result.success:
                    # After refresh, check if there are any resources left
                    try:
                        stack_state = stack.export_stack()
                        resources = stack_state.deployment.get("resources", []) if stack_state.deployment else []
                        
                        # Filter out the root stack resource - it's always present
                        actual_resources = [r for r in resources if r.get("type") != "pulumi:pulumi:Stack"]
                        
                        if len(actual_resources) == 0:
                            # No resources left, consider this a successful destroy
                            exec_result = ExecResult(
                                success=True,
                                return_code=0,
                                stdout=f"Stack '{self.stack_name}' has no resources after refresh. Treating as successfully destroyed.",
                                stderr="",
                            )
                            # Create a fake summary for consistency
                            exec_result.result = type('obj', (object,), {'result': 'succeeded'})()
                            return exec_result
                        else:
                            # Resources still exist, retry destroy
                            result = stack.destroy()
                            exec_result = ExecResult(
                                success=True if result.summary.result == "succeeded" else False,
                                return_code=0 if result.summary.result == "succeeded" else 1,
                                stdout=result.stdout,
                                stderr=result.stderr,
                            )
                            exec_result.result = result.summary
                            return exec_result
                    except Exception as retry_error:
                        # If retry fails, return the original error plus context
                        return ExecResult(
                            success=False,
                            return_code=1,
                            stdout="",
                            stderr=f"Refresh succeeded but destroy retry failed: {str(retry_error)}. Original error: {error_msg}",
                        )
                else:
                    # Refresh failed, return original error
                    return ExecResult(
                        success=False,
                        return_code=1,
                        stdout="",
                        stderr=f"Failed to refresh stack state: {refresh_result.stderr}. Original error: {error_msg}",
                    )
            else:
                # Not a sync issue, return original error
                return ExecResult(
                    success=False,
                    return_code=1,
                    stdout="",
                    stderr=error_msg,
                )

    def remove(self) -> ExecResult[None]:
        """
        Deletes the stack and all associated configuration and history.

        Note: This should only be called after destroy() has been successfully executed.

        Returns:
            ExecResult indicating success/failure of stack removal
        """
        try:
            stack = self.select_stack()
            if not stack:
                return ExecResult(
                    success=False,
                    return_code=1,
                    stdout="",
                    stderr=f"Stack '{self.stack_name}' does not exist",
                )

            # Check if stack is empty (all resources destroyed)
            # This is a safety check to prevent removing stacks with active resources
            try:
                stack_state = stack.export_stack()
                if (
                    stack_state.deployment
                    and len(stack_state.deployment.get("resources", [])) > 0
                ):
                    error_msg = f"Cannot remove stack '{self.stack_name}': Stack still contains resources. Run destroy() first."
                    return ExecResult(
                        success=False, return_code=1, stdout="", stderr=error_msg
                    )
            except Exception:
                # If we can't check state, proceed with removal
                # (stack might be in corrupted state)
                pass

            # Remove the stack from workspace
            stack.workspace.remove_stack(self.stack_name)

            return ExecResult(
                success=True,
                return_code=0,
                stdout=f"Stack '{self.stack_name}' removed successfully",
                stderr="",
            )

        except auto.StackNotFoundError:
            # Stack doesn't exist - this is fine for removal
            return ExecResult(
                success=True,
                return_code=0,
                stdout=f"Stack '{self.stack_name}' does not exist",
                stderr="",
            )
        except Exception as e:
            error_msg = f"Failed to remove stack '{self.stack_name}': {str(e)}"
            return ExecResult(success=False, return_code=1, stdout="", stderr=error_msg)
