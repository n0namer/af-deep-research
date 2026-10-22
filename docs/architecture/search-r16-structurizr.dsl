workspace "af-deep-research search retrieval" "CANDIDATE / UNACCEPTED source-grounded view" {
    model {
        caller = person "Research caller"
        system = softwareSystem "Deep research search boundary"
        registry = container system "Provider registry" "Priority and availability selection" "Python"
        federation = container system "Federated retrieval" "Bounded concurrent provider calls" "Python"
        fusion = container system "Deterministic fusion" "Canonical URL dedupe and RRF" "Python"
        caller -> system "submits query"
        system -> registry "resolves providers"
        system -> federation "requests bounded retrieval"
        federation -> fusion "fuses successful responses"
    }
    views {
        systemContext system "search-context" { include * autolayout lr }
        container system "search-containers" { include * autolayout lr }
    }
}
