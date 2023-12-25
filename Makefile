IMAGE_NAME = codeberg.org/drunkontee/despot
IMAGE_TAG = dev
BUILD_ARGS =
PLATFORMS = linux/amd64,linux/arm64/v8

.PHONY: build
build:
	docker buildx build \
	--pull \
	$(BUILD_ARGS) \
	--provenance=false \
	--sbom=false \
	--tag $(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: .buildx-builder
.buildx-builder:
	docker buildx create \
	--name crossplatform \
	--node crossplatform0 \
	--platform $(PLATFORMS) || true

.PHONY: build-push
build-push: .buildx-builder
	@$(MAKE) build BUILD_ARGS='$(BUILD_ARGS) --push --builder crossplatform --platform $(PLATFORMS)'
