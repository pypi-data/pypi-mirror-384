import json
import os


def _discover_similar_tools(tool_description, call_tool):
    """Discover similar tools"""
    similar_tools = []

    discovery_methods = [
        ("Tool_Finder_Keyword", {"description": tool_description, "limit": 5})
    ]

    for method_name, args in discovery_methods:
        result = call_tool(method_name, args)
        if result and isinstance(result, list):
            similar_tools.extend(result)

    # Deduplicate
    seen = set()
    deduped_tools = []
    for tool in similar_tools:
        try:
            if isinstance(tool, dict):
                tool_tuple = tuple(sorted(tool.items()))
            elif isinstance(tool, (list, tuple)):
                deduped_tools.append(tool)
                continue
            else:
                tool_tuple = tool

            if tool_tuple not in seen:
                seen.add(tool_tuple)
                deduped_tools.append(tool)
        except (TypeError, AttributeError):
            deduped_tools.append(tool)

    return deduped_tools


def _generate_tool_specification(tool_description, similar_tools, call_tool):
    """Generate tool specification"""
    spec_input = {
        "tool_description": tool_description,
        "tool_category": "general",
        "tool_type": "CustomTool",
        "similar_tools": json.dumps(similar_tools) if similar_tools else "[]",
        "existing_tools_summary": "Available tools: standard ToolUniverse tools",
    }

    result = call_tool("ToolSpecificationGenerator", spec_input)
    if not result or "result" not in result:
        raise RuntimeError("ToolSpecificationGenerator returned invalid result")

    tool_config = result["result"]

    # Ensure tool_config is a dictionary
    if isinstance(tool_config, str):
        try:
            tool_config = json.loads(tool_config)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse tool_config JSON: {tool_config}")
    elif not isinstance(tool_config, dict):
        raise TypeError(
            f"tool_config must be a dictionary, " f"got: {type(tool_config)}"
        )

    return tool_config


def _generate_implementation(tool_config, call_tool):
    """Generate implementation code for all tool types"""
    if "implementation" in tool_config:
        return tool_config

    impl_input = {
        "tool_description": tool_config.get("description", ""),
        "tool_parameters": json.dumps(tool_config.get("parameter", {})),
        "domain": "general",
        "complexity_level": "intermediate",
    }

    # Try multiple times to generate implementation
    for attempt in range(3):
        try:
            print(
                f"🔄 Attempting to generate implementation code "
                f"(attempt {attempt + 1}/3)..."
            )
            result = call_tool("ToolImplementationGenerator", impl_input)

            if result and "result" in result:
                result_data = result["result"]
                if isinstance(result_data, str):
                    try:
                        impl_data = json.loads(result_data)
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON parsing failed: {e}")
                        continue
                else:
                    impl_data = result_data

                if (
                    "implementation" in impl_data
                    and "source_code" in impl_data["implementation"]
                ):
                    tool_config["implementation"] = impl_data["implementation"]
                    print("✅ Successfully generated implementation code")
                    return tool_config
                else:
                    missing_fields = list(impl_data.get("implementation", {}).keys())
                    print(
                        f"⚠️ Generated implementation missing required "
                        f"fields: {missing_fields}"
                    )
            else:
                print("⚠️ ToolImplementationGenerator returned invalid result")

        except Exception as e:
            print(
                f"❌ Error generating implementation code "
                f"(attempt {attempt + 1}/3): {e}"
            )
            continue

    return tool_config


def _generate_test_cases(tool_config, call_tool):
    """Generate test cases"""
    test_input = {"tool_config": tool_config}

    for attempt in range(5):
        try:
            result = call_tool("TestCaseGenerator", test_input)
            if result and "result" in result:
                result_data = result["result"]
                if isinstance(result_data, str):
                    test_data = json.loads(result_data)
                else:
                    test_data = result_data

                if "test_cases" in test_data:
                    test_cases = test_data["test_cases"]
                    if _validate_test_cases(test_cases, tool_config):
                        return test_cases
        except Exception as e:
            print(f"🔧 TestCaseGenerator attempt #{attempt + 1}/5 failed: {e}")
            continue

    return []


def _validate_test_cases(test_cases, tool_config):
    """Validate test cases"""
    if not isinstance(test_cases, list):
        return False

    tool_name = tool_config.get("name", "")
    required_params = tool_config.get("parameter", {}).get("required", [])

    for test_case in test_cases:
        if not isinstance(test_case, dict):
            return False
        if test_case.get("name") != tool_name:
            return False
        args = test_case.get("arguments", {})
        missing_params = [p for p in required_params if p not in args]
        if missing_params:
            return False

    return True


def _execute_test_cases(tool_config, test_cases):
    """Execute test cases to validate code functionality"""
    print("🧪 Executing test cases to validate code functionality...")

    test_results = {
        "total_tests": len(test_cases),
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": [],
        "overall_success_rate": 0.0,
    }

    if not test_cases:
        print("⚠️ No test cases to execute")
        return test_results

    # Dynamic import of generated tool code
    # try:
    # Build tool code file path
    tool_name = tool_config.get("name", "UnknownTool")
    base_filename = f"generated_tool_{tool_config['name']}"
    code_file = f"generated_tool_{tool_name.lower()}_code.py"

    print("💾 Saving tool files for testing...")

    saved_files = _save_tool_files(tool_config, base_filename)
    print(f"Saved: {saved_files}")

    if os.path.exists(code_file):
        # 动态导入工具
        import importlib.util

        spec = importlib.util.spec_from_file_location(tool_name, code_file)
        tool_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool_module)

        # Get tool function
        tool_function = getattr(tool_module, tool_name.lower(), None)

        if tool_function:
            print(f"✅ Successfully imported tool: {tool_name}")

            # Execute each test case
            for i, test_case in enumerate(test_cases):
                test_result = {
                    "test_id": i + 1,
                    "test_case": test_case,
                    "status": "unknown",
                    "result": None,
                    "error": None,
                    "execution_time": 0,
                }

                try:
                    import time

                    start_time = time.time()

                    # Extract test parameters
                    if isinstance(test_case, dict) and "input" in test_case:
                        test_args = test_case["input"]
                    elif isinstance(test_case, dict) and "arguments" in test_case:
                        test_args = test_case["arguments"]
                    else:
                        test_args = test_case

                    # Execute test
                    result = tool_function(test_args)
                    print(f"result: {result}")
                    execution_time = time.time() - start_time

                    # Validate result
                    if result is not None and not isinstance(result, dict):
                        test_result["status"] = "failed"
                        test_result["error"] = "Return value is not a dictionary"
                    elif result is None:
                        test_result["status"] = "failed"
                        test_result["error"] = "Return value is None"
                    else:
                        test_result["status"] = "passed"
                        test_result["result"] = result

                    test_result["execution_time"] = execution_time

                except Exception as e:
                    test_result["status"] = "failed"
                    test_result["error"] = str(e)
                    test_result["execution_time"] = 0

                # Count results
                if test_result["status"] == "passed":
                    test_results["passed_tests"] += 1
                else:
                    test_results["failed_tests"] += 1

                test_results["test_details"].append(test_result)

                # Print test results
                status_emoji = "✅" if test_result["status"] == "passed" else "❌"
                print(f"  {status_emoji} Test {i+1}: {test_result['status']}")
                if test_result["error"]:
                    print(f"     Error: {test_result['error']}")

            # Calculate success rate
            test_results["overall_success_rate"] = (
                (test_results["passed_tests"] / test_results["total_tests"])
                if test_results["total_tests"] > 0
                else 0.0
            )

            passed = test_results["passed_tests"]
            total = test_results["total_tests"]
            print(f"📊 Test execution completed: {passed}/{total} passed")
            print(f"🎯 Success rate: {test_results['overall_success_rate']:.1%}")

        else:
            print(f"❌ Unable to find tool function: {tool_name.lower()}")
            test_results["error"] = f"Tool function not found: {tool_name.lower()}"
    else:
        print(f"❌ Tool code file does not exist: {code_file}")
        test_results["error"] = f"Code file does not exist: {code_file}"

    return test_results


def _evaluate_quality(tool_config, test_cases, call_tool):
    """评估代码质量 - 使用增强的CodeQualityAnalyzer + 实际测试执行"""

    # 首先执行测试样例来验证功能
    test_execution_results = _execute_test_cases(tool_config, test_cases)

    # 提取实现代码
    implementation_code = ""
    if "implementation" in tool_config:
        impl = tool_config["implementation"]
        print("impl.keys():", impl.keys())
        implementation_code = impl["source_code"]

    # Build analysis input including test execution results
    eval_input = {
        "tool_name": tool_config.get("name", "UnknownTool"),
        "tool_description": tool_config.get("description", ""),
        "tool_parameters": json.dumps(tool_config.get("parameter", {})),
        "implementation_code": implementation_code,
        "test_cases": json.dumps(test_cases),
        "test_execution_results": json.dumps(test_execution_results),
    }

    print("🔍 Using CodeQualityAnalyzer for deep code quality analysis...")

    result = call_tool("CodeQualityAnalyzer", eval_input)
    print(f"result: {result['result']}")

    result_data = result["result"]
    parsed_data = json.loads(result_data)
    parsed_data["test_execution"] = test_execution_results

    return parsed_data


def _expand_test_coverage(tool_config, call_tool):
    """Expand test coverage"""
    test_input = {
        "tool_config": tool_config,
        "focus_areas": ["edge_cases", "boundary_conditions", "error_scenarios"],
    }

    result = call_tool("TestCaseGenerator", test_input)
    if result and "result" in result:
        result_data = result["result"]
        if isinstance(result_data, str):
            try:
                test_cases = json.loads(result_data)
                if "test_cases" in test_cases:
                    if "testing" not in tool_config:
                        tool_config["testing"] = {}
                    tool_config["testing"]["test_cases"] = test_cases["test_cases"]
                    return tool_config
            except json.JSONDecodeError:
                pass

    return None


def _optimize_code(tool_config, call_tool, quality_evaluation):
    """General code optimization"""
    optimization_input = {
        "tool_config": json.dumps(tool_config),
        "quality_evaluation": json.dumps(quality_evaluation),
    }

    result = call_tool("CodeOptimizer", optimization_input)

    if result and "result" in result:
        result_data = result["result"]
        optimized = json.loads(result_data)

        # Check return format, CodeOptimizer now returns {"implementation": {...}}
        if "implementation" in optimized:
            tool_config["implementation"] = optimized["implementation"]
        else:
            # Compatible with old format
            tool_config["implementation"] = optimized

        return tool_config


def iterative_code_improvement(
    tool_config, call_tool, max_iterations=5, target_score=9.5
):
    """Iteratively improve code implementation until target quality score is reached"""
    print("\n🚀 Starting iterative code improvement process")
    print(f"Target quality score: {target_score}/10")
    print(f"Maximum iterations: {max_iterations}")

    current_score = 0
    improvement_history = []

    for iteration in range(max_iterations):
        print(f"\n🔄 Iteration {iteration + 1}/{max_iterations}")
        print(f"Current quality score: {current_score:.2f}/10")

        # Generate test cases and evaluate quality
        test_cases = _generate_test_cases(tool_config, call_tool)
        print(f"Generated {len(test_cases)} test cases")

        print(f"test_cases: {test_cases}")

        quality_evaluation = _evaluate_quality(tool_config, test_cases, call_tool)
        new_score = quality_evaluation.get("overall_score", 0)

        print(f"Quality evaluation result: {new_score:.2f}/10")
        if "scores" in quality_evaluation:
            for aspect, score in quality_evaluation["scores"].items():
                print(f"  - {aspect}: {score:.2f}/10")

        # Check if target is reached
        if new_score >= target_score:
            print(f"🎉 Target quality score {target_score}/10 reached!")
            improvement_history.append(
                {
                    "iteration": iteration + 1,
                    "score": new_score,
                    "improvement": new_score - current_score,
                    "status": "target_achieved",
                }
            )
            break

        # Record improvement
        improvement = new_score - current_score
        print(f"Improvement: {improvement:+.2f}")

        improvement_history.append(
            {
                "iteration": iteration + 1,
                "score": new_score,
                "improvement": improvement,
                "status": "improved",
            }
        )
        current_score = new_score

        tool_config = _optimize_code(tool_config, call_tool, quality_evaluation)

    # Final quality evaluation
    final_test_cases = _generate_test_cases(tool_config, call_tool)
    final_quality = _evaluate_quality(tool_config, final_test_cases, call_tool)
    final_score = final_quality.get("overall_score", current_score)

    print("🏁 Iterative improvement completed")
    print(f"Final quality score: {final_score:.2f}/10")
    print(f"Total iterations: {len(improvement_history)}")

    print("\n📈 Improvement history:")
    for record in improvement_history:
        status_emoji = "🎯" if record["status"] == "target_achieved" else "📈"
        print(
            f"  {status_emoji} Round {record['iteration']}: {record['score']:.2f}/10 (improvement: {record['score']:+.2f})"
        )

    return tool_config, final_score, improvement_history


def _save_tool_files(tool_config, base_filename):
    """Save tool files"""
    # Update configuration
    config_to_save = tool_config.copy()
    class_name = config_to_save.get("name", "CustomTool")
    config_to_save["type"] = class_name

    # Extract dependency information
    dependencies = []
    if (
        "implementation" in tool_config
        and "dependencies" in tool_config["implementation"]
    ):
        dependencies = tool_config["implementation"]["dependencies"]

    # Add dependencies field to configuration
    config_to_save["dependencies"] = dependencies

    # Remove implementation code
    if "implementation" in config_to_save:
        del config_to_save["implementation"]

    # Save configuration file
    config_file = f"{base_filename}_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_to_save, f, indent=2, ensure_ascii=False)

    # Generate code file
    code_file = f"{base_filename}_code.py"
    _generate_tool_code(tool_config, code_file)

    return [config_file, code_file]


def _convert_json_to_python(obj):
    """Recursively convert JSON object booleans and types to Python format"""
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            result[key] = _convert_json_to_python(value)
        return result
    elif isinstance(obj, list):
        return [_convert_json_to_python(item) for item in obj]
    elif obj == "true":
        return True
    elif obj == "false":
        return False
    elif obj == "string":
        return str
    elif obj == "number":
        return float
    elif obj == "integer":
        return int
    elif obj == "object":
        return dict
    elif obj == "array":
        return list
    else:
        return obj


def _convert_python_types_to_strings(obj):
    """Recursively convert Python type objects to string representations for JSON serialization"""
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            result[key] = _convert_python_types_to_strings(value)
        return result
    elif isinstance(obj, list):
        return [_convert_python_types_to_strings(item) for item in obj]
    elif obj is True:
        return "True"
    elif obj is False:
        return "False"
    elif obj is str:
        return "str"
    elif obj is float:
        return "float"
    elif obj is int:
        return "int"
    elif obj is dict:
        return "dict"
    elif obj is list:
        return "list"
    else:
        return obj


def _generate_tool_code(tool_config, code_file):
    """Generate Python code for all tool types using correct register_tool method"""
    tool_name = tool_config["name"]

    with open(code_file, "w", encoding="utf-8") as f:
        # Add dependency instructions comment
        if (
            "implementation" in tool_config
            and "dependencies" in tool_config["implementation"]
        ):
            dependencies = tool_config["implementation"]["dependencies"]
            if dependencies:
                f.write("# Required packages:\n")
                for dep in dependencies:
                    f.write(f"# pip install {dep}\n")
                f.write("\n")

        f.write("from typing import Dict, Any\n")
        f.write("from src.tooluniverse import register_tool\n\n")

        # Import dependencies
        if (
            "implementation" in tool_config
            and "imports" in tool_config["implementation"]
        ):
            for imp in tool_config["implementation"]["imports"]:
                f.write(f"{imp}\n")

        f.write("\n")

        # Generate function implementation directly, no classes
        f.write("@register_tool(\n")
        f.write(f'    "{tool_name}",\n')
        f.write("    {\n")
        f.write(f'        "name": "{tool_name}",\n')
        f.write(f'        "type": "{tool_name}",\n')
        f.write(f'        "description": "{tool_config.get("description", "")}",\n')

        # Use helper functions to convert JSON booleans and types to Python format
        parameter_json = _convert_json_to_python(tool_config.get("parameter", {}))
        # Convert Python type objects to string representations
        parameter_json_str = _convert_python_types_to_strings(parameter_json)
        f.write(f'        "parameter": {json.dumps(parameter_json_str, indent=8)},\n')

        return_schema_json = _convert_json_to_python(
            tool_config.get("return_schema", {})
        )
        # Convert Python type objects to string representations
        return_schema_json_str = _convert_python_types_to_strings(return_schema_json)
        f.write(
            f'        "return_schema": {json.dumps(return_schema_json_str, indent=8)},\n'
        )

        # Add dependency information
        if (
            "implementation" in tool_config
            and "dependencies" in tool_config["implementation"]
        ):
            dependencies = tool_config["implementation"]["dependencies"]
            f.write(f'        "dependencies": {json.dumps(dependencies, indent=8)}\n')
        else:
            f.write('        "dependencies": []\n')

        f.write("    }\n")
        f.write(")\n")
        f.write(
            f"def {tool_name.lower()}(arguments: Dict[str, Any]) -> Dict[str, Any]:\n"
        )
        f.write(f'    """{tool_config.get("description", "")}"""\n')
        f.write("    try:\n")

        # Add source code
        if (
            "implementation" in tool_config
            and "source_code" in tool_config["implementation"]
        ):
            source_code = tool_config["implementation"]["source_code"]
            f.write("        # Generated implementation:\n")
            for line in source_code.split("\n"):
                if line.strip():  # Skip empty lines
                    f.write(f"        {line}\n")
                else:
                    f.write("\n")

            # Ensure execute_tool is called and result is returned
            f.write("        \n")
            f.write("        # Execute the tool and return result\n")
            f.write("        return execute_tool(arguments)\n")
        else:
            # Default implementation
            f.write("        result = {\n")
            f.write('            "status": "success",\n')
            f.write('            "message": "Tool executed successfully",\n')
            f.write('            "input": arguments\n')
            f.write("        }\n")
            f.write("        return result\n")

        f.write("    except Exception as e:\n")
        f.write('        return {"error": str(e)}\n')


def compose(arguments, tooluniverse, call_tool):
    """General tool discovery and generation system"""
    tool_description = arguments["tool_description"]
    max_iterations = arguments.get("max_iterations", 2)
    arguments.get("save_to_file", True)

    print(f"🔍 Starting tool discovery: {tool_description}")

    # 1. Discover similar tools
    print("📊 Discovering similar tools...")
    similar_tools = _discover_similar_tools(tool_description, call_tool)
    print(f"Found {len(similar_tools)} similar tools")

    # 2. Generate initial tool specification
    print("🏗️ Generating tool specification...")
    tool_config = _generate_tool_specification(
        tool_description, similar_tools, call_tool
    )

    # 3. Generate implementation for all tools
    print("💻 Generating code implementation...")
    tool_config = _generate_implementation(tool_config, call_tool)

    # 4. Iterative optimization
    print("\n🚀 Starting enhanced iterative improvement system...")

    target_quality_score = arguments.get("target_quality_score", 8.5)

    print(
        f"🎯 Enabling iterative improvement, target quality score: {target_quality_score}/10"
    )

    tool_config, final_quality_score, improvement_history = iterative_code_improvement(
        tool_config,
        call_tool,
        max_iterations=max_iterations,
        target_score=target_quality_score,
    )

    print(
        f"🎉 Iterative improvement completed! Final quality score: {final_quality_score:.2f}/10"
    )

    # 5. Save tool files
    print("💾 Saving tool files...")
    base_filename = f"generated_tool_{tool_config['name']}"
    saved_files = _save_tool_files(tool_config, base_filename)
    print(f"Saved: {saved_files}")

    print("\n🎉 Tool generation completed!")
    print(f"Tool name: {tool_config['name']}")
    print(f"Tool type: {tool_config['type']}")
    print(f"Final quality: {final_quality_score:.1f}/10")

    return {
        "tool_config": tool_config,
        "quality_score": final_quality_score,
        "saved_files": saved_files,
    }
