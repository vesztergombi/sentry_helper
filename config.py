
regular_repos = \
"""
bitly-link-click-webhook
facebook-dark-post-source
facebook-post-source
facebook-private-message-source
facebook-rating-source
facebook-video-metrics-source
google-my-business-location-source
hearsay-access-token-provider
hearsay-location-sink
hearsay-metrics-sink
hearsay-profile-sink
hearsay-video-source
instagram-dark-post-source
instagram-direct-message-source
instagram-tag-source
instagram-webhook
kaltura-video-metrics-source
linkedin-invitation-source
linkedin-media-register
linkedin-media-upload-status
linkedin-media-uploader
linkedin-organization-metrics-source
linkedin-post-publisher-fail
linkedin-profile-source
linkedin-ugc-publisher
network-activity-attachment-processor
network-activity-sink
twitter-multi-media-publisher
twitter-profile-source
twitter-tweet-source
""".split()

special_repos = \
"""
bitly-link-source
bitly-link-click-source
nap-crawl-service-replayer
network-activity-platform-dlq-router
""".split()

repos = regular_repos

work_dir = '/Users/gvesztergombi/sentry_repos'
