"""
REST API Generator (Placeholder)

This is a placeholder showing how the API system can be extended with new generators.
A REST API generator could be implemented here using FastAPI, Flask, or similar.

Example implementation would:
1. Inherit from BaseGenerator
2. Read method metadata from API_REGISTRY
3. Generate REST routes with proper HTTP methods:
   - GET /api/vms/{vm_id}/status -> status(vm_id)
   - POST /api/vms -> add(config, name)
   - DELETE /api/vms/{vm_id} -> rm(vm_id)
4. Handle request/response serialization
5. Add authentication/authorization if needed

Usage:
    from maqet.generators import RestAPIGenerator
    generator = RestAPIGenerator(maqet_instance, API_REGISTRY)
    app = generator.generate()  # Returns FastAPI/Flask app
"""

from ..api import APIRegistry
from .base_generator import BaseGenerator


class RestAPIGenerator(BaseGenerator):
    """
    Placeholder REST API generator demonstrating extensibility.

    A real implementation would generate REST endpoints from @api_method
    decorated methods, handling routing, serialization, and validation.
    """

    def generate(self):
        """
        Generate REST API routes.

        Returns:
            Web application instance (FastAPI, Flask, etc.)
        """
        raise NotImplementedError(
            "REST API generation not yet implemented. "
            "This is a placeholder demonstrating the extensible architecture."
        )

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Run the REST API server.

        Args:
            host: Server host
            port: Server port
        """
        raise NotImplementedError(
            "REST API server not yet implemented. "
            "This would start a web server with generated routes."
        )
