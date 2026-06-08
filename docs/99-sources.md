# 99 — Sources & Freshness Notes

Grouped by topic. **Freshness caveat:** `developer.walmart.com` is a JavaScript SPA, so some pages render thin to automated fetch; several exact field spellings, header casings, and per‑endpoint rate numbers were corroborated against Walmart's Postman collection and the community OpenAPI/SDK mirrors below. **Before coding, confirm exact request/response schemas against a live sandbox call.** Where sources conflicted, the doc flags it inline.

## Access, auth & Connected Apps
- https://developer.walmart.com/us-marketplace/docs/get-started-as-a-seller
- https://developer.walmart.com/us-marketplace/docs/get-started-as-a-solution-provider
- https://developer.walmart.com/us-marketplace/docs/authentication-authorization
- https://developer.walmart.com/us-marketplace/docs/oauth-authentication
- https://developer.walmart.com/us-marketplace/docs/oauth-20-authorization
- https://developer.walmart.com/doc/us/mp/us-mp-auth2/
- https://developer.walmart.com/us-marketplace/reference/tokenapi
- https://developer.walmart.com/us-marketplace/docs/delegated-access-authorization
- https://developer.walmart.com/us-marketplace/docs/walmart-marketplace-api-deprecation-guide
- https://developer.walmart.com/faq/us/faq-auth/
- https://marketplacelearn.walmart.com/guides/Getting%20started/Getting%20ready%20to%20sell/connect-a-solution-provider-in-seller-center
- https://marketplacelearn.walmart.com/guides/Getting%20started/Getting%20ready%20to%20sell/Choose-a-solution-provider
- https://marketplacelearn.walmart.com/guides/Getting%20started/Getting%20ready%20to%20sell/Integration-methods-API
- https://marketplace.walmart.com/channel-partner-prospect-form/
- https://gotrellis.com/resources/blog/walmart-marketplace-app-store-guide/
- https://www.geekseller.com/blog/walmarts-oauth-and-delegated-access-features-for-marketplace/
- https://help.sellercloud.com/omnichannel-ecommerce/walmart-marketplace-account-integration/

## API fundamentals & rate limits
- https://developer.walmart.com/us-marketplace/docs/introduction-to-marketplace-apis
- https://developer.walmart.com/us-marketplace/docs/rate-limiting
- https://developer.walmart.com/doc/us/mp/us-mp-throttling/
- https://developer.walmart.com/us-marketplace/docs/error-codes
- https://support.geekseller.com/knowledgebase/walmart-api-limits/

## Items / Catalog
- https://developer.walmart.com/doc/us/mp/us-mp-items/
- https://developer.walmart.com/us-marketplace/docs/get-item-details
- https://developer.walmart.com/us-marketplace/docs/retire-an-item
- https://developer.walmart.com/us-marketplace/page/bulk-item-delete
- https://developer.walmart.com/cl-marketplace/reference/bulkitemsetup
- https://developer.walmart.com/us-marketplace/docs/item-setup-schema-key-points
- https://developer.walmart.com/us-marketplace/docs/item-search-for-the-walmart-catalog
- https://developer.walmart.com/us-marketplace/docs/walmart-catalog-item-search
- https://developer.walmart.com/us-marketplace/docs/limit-and-pagination
- https://developer.walmart.com/us-marketplace/reference/getspec
- https://developer.walmart.com/us-marketplace/docs/get-item-setup-requirements
- https://developer.walmart.com/us-marketplace/reference/gettaxonomyresponse-1
- https://developer.walmart.com/us-marketplace/docs/utilities-overview
- https://developer.walmart.com/us-marketplace/page/item-spec-version-update-and-new-features
- https://developer.walmart.com/us-marketplace/docs/item-setup-sla-and-exceptions
- https://developer.walmart.com/us-marketplace/docs/monitor-my-item
- https://sellercloud.com/blog/walmart-item-spec-5/
- https://www.sellbrite.com/blog/walmart-item-spec-5-0/
- https://goaura.com/blog/walmart-rich-media-and-image-guidelines
- https://marketplacelearn.walmart.com/guides/Item%20setup/Item%20content,%20imagery,%20and%20media/Product-detail-page:-Image-guidelines-&-requirements

## Feeds
- https://developer.walmart.com/doc/us/mp/us-mp-feeds/
- https://developer.walmart.com/us-marketplace/reference/getallfeedstatuses
- https://developer.walmart.com/us-marketplace/docs/list-all-feed-statuses

## Inventory & lag time
- https://developer.walmart.com/us-marketplace/docs/inventory-api-overview
- https://developer.walmart.com/doc/us/mp/us-mp-inventory
- https://developer.walmart.com/us-marketplace/reference/getinventory
- https://developer.walmart.com/us-marketplace/reference/updateinventoryforanitem
- https://developer.walmart.com/us-marketplace/reference/getmultinodeinventoryforskuandallshipnodes
- https://developer.walmart.com/us-marketplace/reference/updatemultinodeinventory
- https://developer.walmart.com/us-marketplace/docs/update-lag-time-for-an-item
- https://developer.walmart.com/us-marketplace/docs/lag-time-api-overview
- https://docs.datavirtuality.com/connectors/walmart-marketplace-reference

## Price, promotions & repricer
- https://developer.walmart.com/us-marketplace/docs/price-and-promotional-price-management-api-overview
- https://developer.walmart.com/us-marketplace/reference/updatepromotionalprices
- https://developer.walmart.com/us-marketplace/docs/update-promotional-price-for-a-single-item
- https://developer.walmart.com/us-marketplace/reference/post_v3-feeds-feedtype-price-and-promotion
- https://developer.walmart.com/us-marketplace/docs/update-promotional-pricing-for-multiple-items-in-bulk
- https://developer.walmart.com/us-marketplace/docs/repricer-strategy-api-overview
- https://developer.walmart.com/us-marketplace/reference/updatestrategy
- https://developer.walmart.com/us-marketplace/docs/repricing-during-item-setup
- https://marketplacelearn.walmart.com/guides/Catalog%20management/Price%20management/Repricer:-overview
- https://marketplacelearn.walmart.com/guides/Catalog%20management/Price%20management/Repricer:-Create-a-strategy
- https://www.selleractive.com/e-commerce-blog/walmart-marketplace-buy-box-webhooks
- https://www.flashpricer.com/post/the-data-problem-costing-walmart-sellers-the-buy-box
- https://sellersnap.io/walmart-repricing-strategies/

## Orders
- https://developer.walmart.com/doc/us/mp/us-mp-orders/
- https://developer.walmart.com/us-marketplace/docs/get-all-released-orders
- https://developer.walmart.com/us-marketplace/docs/get-all-orders
- https://developer.walmart.com/us-marketplace/docs/get-an-order
- https://marketplacelearn.walmart.com/guides/Policies%20&%20standards/Shipping%20&%20fulfillment/Shipping-and-fulfillment-policy
- https://marketplacelearn.walmart.com/guides/Shipping%20&%20fulfillment/Shipping%20methods/Shipping-methods:-parcel-shipping-carriers
- https://marketplacelearn.walmart.com/guides/Policies%20&%20standards/Shipping%20&%20fulfillment/Valid-tracking-number-policy
- https://marketplacelearn.walmart.com/guides/Order%20management/Order%20status/Update-tracking-numbers-in-Seller-Center

## Returns
- https://developer.walmart.com/us-marketplace/docs/returns-and-refunds-api-overview
- https://developer.walmart.com/us-marketplace/reference/issuerefund
- https://developer.walmart.com/us-marketplace/docs/issue-a-refund
- https://developer.walmart.com/api/us/mp/returns
- https://developer.walmart.com/us-marketplace/docs/create-return-for-customer-order-for-wfs-item
- https://developer.walmart.com/us-marketplace/reference/getreturnordersstatus
- https://developer.walmart.com/us/whats-new/marketplace-return-item-overrides-report/
- https://marketplacelearn.walmart.com/guides/Order%20management/Returns%20&%20refunds/returns-policy
- https://marketplacelearn.walmart.com/guides/Order%20management/Returns%20&%20refunds/Issue-adjustments-or-non-standard-refunds-in-Seller-Center
- https://marketplacelearn.walmart.com/guides/Policies%20&%20standards/Orders%20&%20returns/Dispute-standards

## WFS / Fulfillment / MCS
- https://developer.walmart.com/us-marketplace/docs/walmart-fulfillment-services-wfs-api-overview
- https://developer.walmart.com/us-marketplace/docs/create-an-inbound-shipment-order-io
- https://developer.walmart.com/us-marketplace/docs/create-customer-order-for-wfs-item
- https://developer.walmart.com/us-marketplace/docs/multichannel-solutions
- https://developer.walmart.com/us-marketplace/page/new-wfs-preferred-carrier-apis
- https://developer.walmart.com/us-marketplace/docs/walmart-preferred-carriers
- https://developer.walmart.com/documentation/get-wfs-inventory-health-report/
- https://developer.walmart.com/doc/us/mp/us-mp-settings/
- https://marketplacelearn.walmart.com/guides/Getting%20started/Walmart%20Fulfillment%20Services%20(WFS)/API-calls-for-WFS
- https://marketplacelearn.walmart.com/guides/Walmart%20Fulfillment%20Services%20(WFS)/Walmart%20Multichannel%20Solutions/multichannel-api
- https://marketplace.walmart.com/walmart-fulfillment-services/

## Reports, Insights & Settlement
- https://developer.walmart.com/doc/us/mp/us-mp-onrequestreports/
- https://developer.walmart.com/us-marketplace/docs/request-an-item-report
- https://developer.walmart.com/us-marketplace/docs/request-an-item-performance-report
- https://developer.walmart.com/us-marketplace/docs/request-a-buybox-insights-report
- https://developer.walmart.com/us-marketplace/docs/request-a-cancellation-report
- https://developer.walmart.com/us-marketplace/docs/insights-api-overview
- https://developer.walmart.com/us-marketplace/page/new-pro-seller-api-available
- https://developer.walmart.com/doc/us/mp/us-mp-assortmentrecommendations/
- https://developer.walmart.com/us-marketplace/docs/recon-report
- https://developer.walmart.com/us-marketplace/docs/recon-report-json
- https://developer.walmart.com/us-marketplace/docs/marketplace-payment-reports-overview
- https://marketplacelearn.walmart.com/guides/Taxes%20&%20payments/Payments/Payment-statements-and-transactions
- https://support.a2xaccounting.com/en/articles/4300567-getting-started-with-a2x-for-walmart

## Notifications / Webhooks
- https://developer.walmart.com/doc/us/mp/us-mp-notifications/
- https://developer.walmart.com/us-marketplace/docs/performance-webhook
- https://developer.walmart.com/documentation/subscribe-to-report-ready-notification/

## Policy, scorecard & pricing rules
- https://marketplacelearn.walmart.com/guides/Policies%20&%20standards/Performance/Seller-performance-standards
- https://marketplacelearn.walmart.com/guides/Catalog%20management/Price%20management/Pricing-rules
- https://marketplacelearn.walmart.com/guides/Catalog%20management/Troubleshooting/Troubleshoot-unpublished-items
- https://marketplacelearn.walmart.com/guides/Catalog%20management/Troubleshooting/Submit-an-external-price-match
- https://marketplacelearn.walmart.com/guides/Item%20setup/Item%20content,%20imagery,%20and%20media/Product-detail-page:-the-buy-box
- https://marketplacelearn.walmart.com/guides/Policies%20&%20standards/Prohibited%20products%20&%20brands/Prohibited-products-policy:-overview
- https://marketplacelearn.walmart.com/guides/Policies%20&%20standards/Performance/Marketplace-Seller-Code-of-Conduct
- https://marketplacelearn.walmart.com/guides/Policies%20&%20standards/Orders%20&%20returns/no-haggling-policy
- https://marketplacelearn.walmart.com/guides/Policies%20&%20standards/Troubleshooting/Appeal-an-account-suspension
- https://riverbendconsulting.com/blog/walmart-pricing-rules/
- https://www.zentail.com/blog/how-to-avoid-walmart-marketplace-suspension

## Walmart Connect (advertising)
- https://developer.walmart.com/advertising-partners-search/docs/introduction-to-walmart-connect-ads-apis
- https://developer.walmart.com/advertising-partners/docs/partner-types-and-api-access
- https://www.walmartconnect.com/partners
- https://www.walmartconnect.com/resources/articles/2025/partner-network-display-advertising-api

## Agent tooling / MCP / SDKs
- https://github.com/highsidelabs/walmart-api-php  (community PHP SDK; mirrors v3 paths, may lag releases)
- https://github.com/whitebox-co/walmart-marketplace-api  (community TS client; STALE — last release Dec 2022)
- https://www.npmjs.com/package/@mediocre/walmart-marketplace
- https://github.com/api-evangelist/walmart  (OpenAPI mirrors; third‑party)
- https://www.postman.com/api-evangelist/walmart  (third‑party Postman workspace, NOT official)
- https://vinkius.com/apps/walmart-marketplace-mcp/with/claude-code  (proprietary, paid, NOT Walmart‑affiliated)
- https://github.com/taazkareem/walmart-mcp , https://github.com/markswendsen-code/mcp-walmart  (consumer‑shopping MCPs, not seller API)

## MCP / agent security best practices (for the tool layer)
- https://labs.cloudsecurityalliance.org/agentic/agentic-mcp-security-best-practices-v1/
- https://thenewstack.io/15-best-practices-for-building-mcp-servers-in-production/
- https://www.descope.com/blog/post/mcp-server-security-best-practices

## Integration architecture (real‑time data, multichannel)
- https://rollout.com/integration-guides/walmart/quick-guide-to-realtime-data-in-walmart-without-webhooks
- https://netalith.com/blogs/e-commerce-strategy/walmart-marketplace-integration-inventory-automation-guide
- https://www.channelengine.com/ecommerce-product-listing-software
- https://www.linnworks.com/features/multichannel-listings/
