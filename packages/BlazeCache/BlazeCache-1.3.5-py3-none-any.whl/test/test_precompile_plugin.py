import blazecache.blazecache as blazecache

if __name__ == "__main__":
    lark_repo_code_dir = {
        "aha": "/Users/bytedance/Desktop/lark/src",
        "iron": "/Users/bytedance/Desktop/lark/src/aha/iron"
    }
    lark_feature_branch = {
        "aha": "hkx/test_cherry-pick-error",
        "iron": "dev"
    }
    fallback_branch = {
        "aha": "ci-verify/mr-7621483",
        "iron": "dev"
    }
    mr_target_branch = {
        "aha": "m131",
        "iron": "dev"
    }
    base_commit = {
        "aha": "ebbb66ecf5a23e6901cbc2360f8c4f419e0f1bdf",
        "iron": "da8769a2c519a811068c7a314a1c0269b6cbd266"
    }
    label_name = "mac_arm64_aha_ebbb66ec_iron_da8769a2"
    bccache = blazecache.BlazeCache(product_name="lark", build_dir="/Users/bytedance/Desktop/lark/src/",
                                    local_repo_dir=lark_repo_code_dir, os_type="darwin", branch_type="main", task_type="ci_check_task",
                                    machine_id="123456", ninja_exe_path="/Users/bytedance/Desktop/lark/depot_tools/ninja",
                                    mr_target_branch=mr_target_branch, feature_branch=lark_feature_branch, p4_client="test-ci-check", fallback_branch=fallback_branch, product_tos_url="https://tosv.byted.org/obj/blazecache-cn/product_config/lark/product_config.json")
    bccache.run_precompile_plugin(mr_id="1234", base_commit=base_commit, label_name=label_name)
    # print(bccache.run_postcompile_plugin())