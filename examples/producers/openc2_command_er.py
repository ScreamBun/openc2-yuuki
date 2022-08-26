import time
import uuid

query_features = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "query",
                "target": {
                    "features": ["profiles"]
                }
            }
        }
    }
}

query_features_silent = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "query",
                "target": {
                    "features": ["profiles"]
                },
                "args": {
                    "response_requested" : "none"
                }
            }
        }
    }
}




set_account_status_enabled = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "set",
                "target": {
                    "account": {
                        "uid" : "S-1-5-21-7375663-6890924511-1272660413-2944159"
                        }
                },
                "args": {
                    "account_status" : "enabled",
                    "response_requested": "status",
                    "downstream_device": "False"
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}

set_account_status_disabled = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "set",
                "target": {
                    "account": {
                        "uid" : "S-1-5-21-7375663-6890924511-1272660413-2944159"
                        }
                },
                "args": {
                    "account_status" : "disabled",
                    "response_requested": "status",
                    "downstream_device": "False"
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}

allow_file = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "allow",
                "target": {
                    "file": {
                        "name" : "working1"
                        }
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}

allow_device = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "allow",
                "target": {
                    "device": {
                        "hostname": "DESKTOP-123ABC"
                        }
                },
                "args": {
                    "er": {
                        "device_containment": "app_restriction"
                    }
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}


contain_file = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "set",
                "target": {
                    "account": {
                        "uid" : "S-1-5-21-7375663-6890924511-1272660413-2944159"
                        }
                },
                "args": {
                    "account_status" : "enabled",
                    "response_requested": "status"
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}




create_registry_entry = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "set",
                "target": {
                    "account": {
                        "uid" : "S-1-5-21-7375663-6890924511-1272660413-2944159"
                        }
                },
                "args": {
                    "account_status" : "enabled",
                    "response_requested": "status"
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}

contain_device = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "contain",
                "target": {
                    "device": {
                        "hostname": "DESKTOP-123ABC"
                    }
                },
                "args": {
                    "er": {
                        "device_containment" : "network_isolation"
                    }
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}

contain_device_with_permitted = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "contain",
                "target": {
                    "device": {
                        "hostname": "DESKTOP-123ABC"
                    }
                },
                "args": {
                    "er": {
                        "device_containment": "network_isolation",
                        "permitted_addresses": {
                            "ipv_net": ["192.168.0.255"],
                            "domain_name": ["support.organization.tld", "wiki.organization.tld"]
                        }
                    }
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}

deny_file = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "deny",
                "target": {
                    "file": {
                        "hashes": {
                            "sha256": "0a73291ab5607aef7db23863cf8e72f55bcb3c273bb47f00edf011515aeb5894"
                        }
                    }
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}

deny_ipv4_net = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "deny",
                "target": {
                    "file": {
                        "hashes": {
                            "sha256": "0a73291ab5607aef7db23863cf8e72f55bcb3c273bb47f00edf011515aeb5894"
                        }
                    }
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}

deny_ipv6_net = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "deny",
                "target": {
                    "ipv6_net": "3ffe:1900:4545:3:200:f8ff:fe21:67cf"
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}

deny_ipv4_connection = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "deny",
                "target": {
                    "ipv4_connection": {
                        "protocol": "tcp",
                        "src_port": 21
                    }
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}

deny_ipv6_connection = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "deny",
                "target": {
                    "protocol": "tcp",
                    "dst_addr": "3ffe:1900:4545:3::f8ff:fe21:67cf",
                    "src_port": 21
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}

update_file = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "update",
                "target": {
                    "file": {
                        "uid" : "S-1-5-21-7375663-6890924511-1272660413-2944159"
                        }
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}


stop_process = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "stop",
                "target": {
                    "process": {
                        "uid" : "S-1-5-21-7375663-6890924511-1272660413-2944159"
                        }
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}


stop_device = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "stop",
                "target": {
                    "device": {
                        "uid" : "S-1-5-21-7375663-6890924511-1272660413-2944159"
                        }
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}


stop_service = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "stop",
                "target": {
                    "service": {
                        "uid" : "S-1-5-21-7375663-6890924511-1272660413-2944159"
                        }
                },
                "actuator": {
                    "er": {}
                }
            }
        }
    }
}