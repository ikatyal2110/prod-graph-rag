.PHONY: up down load eval smoke smoke-docker eval-docker clean check-docker

# Check if Docker daemon is running
check-docker:
	@docker info >/dev/null 2>&1 || (echo "Docker daemon not running. Start Docker Desktop and retry." && exit 1)

# Start all services
up: check-docker
	docker compose up -d

# Stop all services and remove volumes
down: check-docker
	docker compose down -v

# Load graph into Neo4j
load: check-docker
	docker compose exec api bash -c "cd /app/graph_rag_api && python scripts/load_graph.py"

# Run both eval sets (against local API, default http://127.0.0.1:8000)
eval:
	python eval/run_eval.py --gold eval/golden_queries.jsonl --k 5 --base-url http://127.0.0.1:8000
	python eval/run_eval.py --gold eval/golden_queries_hard.jsonl --k 5 --base-url http://127.0.0.1:8000

# Run evals against containerized API (depends on up)
eval-docker: up
	python eval/run_eval.py --gold eval/golden_queries.jsonl --k 5 --base-url http://127.0.0.1:8000
	python eval/run_eval.py --gold eval/golden_queries_hard.jsonl --k 5 --base-url http://127.0.0.1:8000

# Smoke test: health check and one /ask query (against local API)
smoke:
	@echo "Checking /health endpoint..."
	@curl -s http://127.0.0.1:8000/health | python -m json.tool || (echo "Health check failed" && exit 1)
	@echo ""
	@echo "Testing /ask endpoint..."
	@curl -s -X POST http://127.0.0.1:8000/ask \
		-H "Content-Type: application/json" \
		-d '{"question": "kubelet crash concurrent map writes"}' | python -m json.tool | head -20 || (echo "Ask query failed" && exit 1)
	@echo ""
	@echo "Smoke test passed!"

# Smoke test against containerized API (depends on up)
smoke-docker: up
	@echo "Checking /health endpoint..."
	@curl -s http://127.0.0.1:8000/health | python -m json.tool || (echo "Health check failed" && exit 1)
	@echo ""
	@echo "Testing /ask endpoint..."
	@curl -s -X POST http://127.0.0.1:8000/ask \
		-H "Content-Type: application/json" \
		-d '{"question": "kubelet crash concurrent map writes"}' | python -m json.tool | head -20 || (echo "Ask query failed" && exit 1)
	@echo ""
	@echo "Smoke test passed!"

# Clean up everything
clean: check-docker
	docker compose down -v
	docker compose rm -f
	docker volume rm prod-graph-rag_neo4j_data prod-graph-rag_neo4j_logs 2>/dev/null || true

