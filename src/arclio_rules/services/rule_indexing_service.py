# import os
# from datetime import datetime
# from typing import Any, Dict

# import frontmatter
# from elasticsearch import AsyncElasticsearch

# from arclio_rules.services.rule_fetch_service import RuleStorageService

# rule_storage_service = RuleStorageService(config={})


# class RuleIndexingService:
#     def __init__(self, config):
#         """Initialize the RuleIndexingService.

#         Args:
#             config (dict): Configuration dictionary containing necessary parameters.
#         """
#         # Initialize Elasticsearch client
#         es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
#         self.es = AsyncElasticsearch([es_url])
#         self.index_name = "arclio-rules"
#         self.config = config

#     async def setup_index(self):
#         """Create the Elasticsearch index with appropriate mappings."""
#         # Check if index exists
#         if not await self.es.indices.exists(index=self.index_name):
#             # Create index with mappings
#             await self.es.indices.create(
#                 index=self.index_name,
#                 body={
#                     "mappings": {
#                         "properties": {
#                             "clientId": {"type": "keyword"},
#                             "path": {"type": "keyword"},
#                             "displayPath": {
#                                 "type": "text",
#                                 "fields": {"keyword": {"type": "keyword"}},
#                             },
#                             "filename": {
#                                 "type": "text",
#                                 "fields": {"keyword": {"type": "keyword"}},
#                             },
#                             "directory": {"type": "keyword"},
#                             "content": {"type": "text"},
#                             "metadata": {
#                                 "properties": {
#                                     "description": {"type": "text"},
#                                     "version": {"type": "keyword"},
#                                     "owner": {"type": "keyword"},
#                                     "last_updated": {"type": "date"},
#                                     "applies_to": {"type": "keyword"},
#                                     "dependencies": {"type": "keyword"},
#                                 }
#                             },
#                             "lastUpdated": {"type": "date"},
#                         }
#                     }
#                 },
#             )

#     async def index_all_rules(self, client_id: str) -> Dict[str, Any]:
#         """Index all rules for a client."""
#         try:
#             await self.setup_index()
#             await self._walk_and_index_directory(client_id, "")
#             return {"success": True}
#         except Exception as e:
#             return {"success": False, "error": str(e)}

#     async def _walk_and_index_directory(self, client_id: str, directory: str):
#         """Recursively walk directory and index all rules."""
#         # TODO : Note the client ID was removed from the list rules function
#         result = await rule_storage_service.list_rules(directory)

#         if not result["success"]:
#             raise Exception(
#                 f"Failed to list rules in {directory}: {result.get('error')}"
#             )

#         for item in result["rules"]:
#             if item["type"] == "dir":
#                 await self._walk_and_index_directory(client_id, item["path"])
#             elif item["type"] == "file" and item["name"].endswith(".mdc"):
#                 await self.index_rule(client_id, item["path"])

#     async def index_rule(self, client_id: str, rule_path: str) -> Dict[str, Any]:
#         """Index a single rule in Elasticsearch."""
#         try:
#             # Get rule content
#             result = await rule_storage_service.get_rule_content(client_id, rule_path)

#             if not result["success"]:
#                 raise Exception(f"Failed to get rule content: {result.get('error')}")

#             content = result["content"]

#             # Parse frontmatter
#             post = frontmatter.loads(content)
#             metadata = post.metadata
#             markdown_content = post.content

#             # Prepare document for indexing
#             doc = {
#                 "clientId": client_id,
#                 "path": rule_path,
#                 "displayPath": f"@{rule_path.replace('.mdc', '')}",
#                 "filename": rule_path.split("/")[-1],
#                 "directory": "/".join(rule_path.split("/")[:-1]),
#                 "content": markdown_content,
#                 "metadata": metadata,
#                 "lastUpdated": datetime.now().isoformat(),
#             }

#             # Index document
#             await self.es.index(
#                 index=self.index_name, id=f"{client_id}:{rule_path}", body=doc
#             )

#             return {"success": True}
#         except Exception as e:
#             return {"success": False, "error": str(e)}

#     async def search_rules(
#         self, client_id: str, query: str, limit: int = 10
#     ) -> Dict[str, Any]:
#         """Search for rules matching query."""
#         try:
#             response = await self.es.search(
#                 index=self.index_name,
#                 body={
#                     "query": {
#                         "bool": {
#                             "must": [
#                                 {"term": {"clientId": client_id}},
#                                 {
#                                     "multi_match": {
#                                         "query": query,
#                                         "fields": [
#                                             "displayPath^3",
#                                             "metadata.description^2",
#                                             "content",
#                                         ],
#                                     }
#                                 },
#                             ]
#                         }
#                     },
#                     "size": limit,
#                 },
#             )

#             # Process results
#             results = []
#             for hit in response["hits"]["hits"]:
#                 source = hit["_source"]
#                 results.append(
#                     {
#                         "id": hit["_id"].split(":")[-1],
#                         "path": source["displayPath"],
#                         "description": source.get("metadata", {}).get(
#                             "description", ""
#                         ),
#                         "score": hit["_score"],
#                     }
#                 )

#             return {"success": True, "results": results}
#         except Exception as e:
#             return {"success": False, "error": str(e)}
