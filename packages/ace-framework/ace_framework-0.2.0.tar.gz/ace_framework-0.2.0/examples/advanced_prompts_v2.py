#!/usr/bin/env python3
"""
Advanced ACE example using v2 prompts with enhanced features.

This demonstrates:
- Using the PromptManager for version control
- Domain-specific prompts (math and code)
- Confidence score tracking
- Prompt output validation
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ace import (
    LiteLLMClient,
    Generator,
    Reflector,
    Curator,
    OfflineAdapter,
    OnlineAdapter,
    Sample,
    TaskEnvironment,
    EnvironmentResult,
    Playbook,
)
from ace.prompts_v2 import (
    PromptManager,
    validate_prompt_output,
    GENERATOR_V2_PROMPT,
    GENERATOR_MATH_PROMPT,
    GENERATOR_CODE_PROMPT
)

# Load environment variables
load_dotenv()


class MathEnvironment(TaskEnvironment):
    """Environment for mathematical problems with detailed validation."""

    def evaluate(self, sample, generator_output):
        """Evaluate mathematical answers with confidence tracking."""
        try:
            # Check if answer is numeric
            expected = float(sample.ground_truth)
            actual = float(generator_output.final_answer)
            correct = abs(expected - actual) < 0.0001

            # Extract confidence if available
            confidence = getattr(generator_output, 'answer_confidence', 0.5)

            return EnvironmentResult(
                feedback=f"Correct! (confidence: {confidence:.2f})" if correct else f"Incorrect. Expected {expected}, got {actual}",
                ground_truth=sample.ground_truth,
                metrics={"accuracy": 1.0 if correct else 0.0, "confidence": confidence}
            )
        except (ValueError, TypeError):
            # Non-numeric answer comparison
            correct = sample.ground_truth.lower() in generator_output.final_answer.lower()
            return EnvironmentResult(
                feedback="Correct!" if correct else f"Incorrect. Expected: {sample.ground_truth}",
                ground_truth=sample.ground_truth,
                metrics={"accuracy": 1.0 if correct else 0.0}
            )


class CodeEnvironment(TaskEnvironment):
    """Environment for code generation tasks."""

    def evaluate(self, sample, generator_output):
        """Evaluate code generation with basic syntax checking."""
        code = generator_output.final_answer

        # Basic Python syntax check
        try:
            compile(code, '<string>', 'exec')
            syntax_valid = True
            feedback = "Code syntax is valid."
        except SyntaxError as e:
            syntax_valid = False
            feedback = f"Syntax error: {e}"

        # Check for required patterns if specified
        contains_required = True
        if hasattr(sample, 'required_patterns'):
            for pattern in sample.required_patterns:
                if pattern not in code:
                    contains_required = False
                    feedback += f" Missing required: {pattern}"

        return EnvironmentResult(
            feedback=feedback,
            ground_truth=sample.ground_truth if hasattr(sample, 'ground_truth') else "",
            metrics={
                "syntax_valid": syntax_valid,
                "contains_required": contains_required
            }
        )


def demo_math_prompts():
    """Demonstrate math-specific v2 prompts."""
    print("\n" + "="*60)
    print("MATH PROMPTS DEMO - Using specialized math generator")
    print("="*60)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY in your .env file")
        return

    # Create prompt manager
    manager = PromptManager(default_version="2.0")

    # Get math-specific prompt
    math_prompt = manager.get_generator_prompt(domain="math")

    # Create LLM client
    llm = LiteLLMClient(model="gpt-3.5-turbo", temperature=0.1)

    # Create math-optimized generator
    math_generator = Generator(llm, prompt_template=math_prompt)

    # Create standard reflector and curator with v2 prompts
    reflector = Reflector(llm, prompt_template=manager.get_reflector_prompt())
    curator = Curator(llm, prompt_template=manager.get_curator_prompt())

    # Create adapter
    adapter = OfflineAdapter(
        playbook=Playbook(),
        generator=math_generator,
        reflector=reflector,
        curator=curator
    )

    # Math problem samples
    samples = [
        Sample(
            question="Solve for x: 2x + 5 = 13",
            ground_truth="4"
        ),
        Sample(
            question="What is 15% of 240?",
            ground_truth="36"
        ),
        Sample(
            question="Find the area of a circle with radius 5 (use π ≈ 3.14159)",
            ground_truth="78.54"
        ),
    ]

    # Run adaptation
    environment = MathEnvironment()
    results = adapter.run(samples, environment, epochs=2)

    # Display results
    print(f"\nTrained on {len(results)} math problems over 2 epochs")
    print(f"Playbook now has {len(adapter.playbook.bullets())} strategies")

    # Show learned strategies
    print("\nLearned Math Strategies:")
    for i, bullet in enumerate(adapter.playbook.bullets()[:3], 1):
        print(f"{i}. {bullet.content[:100]}...")

    # Show usage statistics
    print(f"\nPrompt Usage Stats: {manager.get_stats()}")


def demo_code_prompts():
    """Demonstrate code-specific v2 prompts."""
    print("\n" + "="*60)
    print("CODE PROMPTS DEMO - Using specialized code generator")
    print("="*60)

    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY in your .env file")
        return

    # Create prompt manager
    manager = PromptManager(default_version="2.0")

    # Get code-specific prompt
    code_prompt = manager.get_generator_prompt(domain="code")

    # Create LLM client
    llm = LiteLLMClient(model="gpt-3.5-turbo", temperature=0.1)

    # Create code-optimized generator
    code_generator = Generator(llm, prompt_template=code_prompt)

    # Create components
    adapter = OfflineAdapter(
        playbook=Playbook(),
        generator=code_generator,
        reflector=Reflector(llm, prompt_template=manager.get_reflector_prompt()),
        curator=Curator(llm, prompt_template=manager.get_curator_prompt())
    )

    # Code generation samples
    samples = [
        Sample(
            question="Write a Python function to check if a number is prime",
            ground_truth="def is_prime(n): return n > 1 and all(n % i != 0 for i in range(2, int(n**0.5) + 1))"
        ),
        Sample(
            question="Create a function to reverse a string without using built-in reverse",
            ground_truth="def reverse_string(s): return ''.join(s[i] for i in range(len(s)-1, -1, -1))"
        ),
    ]

    # Run adaptation
    environment = CodeEnvironment()
    results = adapter.run(samples, environment, epochs=1)

    print(f"\nTrained on {len(results)} code problems")
    print(f"Playbook has {len(adapter.playbook.bullets())} code strategies")


def demo_online_learning_with_v2():
    """Demonstrate online learning with v2 prompts and confidence tracking."""
    print("\n" + "="*60)
    print("ONLINE LEARNING DEMO - Real-time adaptation with v2")
    print("="*60)

    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY in your .env file")
        return

    # Create prompt manager
    manager = PromptManager(default_version="2.0")

    # Create LLM client
    llm = LiteLLMClient(model="gpt-3.5-turbo", temperature=0.1)

    # Start with empty playbook
    playbook = Playbook()

    # Create online adapter with v2 prompts
    adapter = OnlineAdapter(
        playbook=playbook,
        generator=Generator(llm, prompt_template=manager.get_generator_prompt()),
        reflector=Reflector(llm, prompt_template=manager.get_reflector_prompt()),
        curator=Curator(llm, prompt_template=manager.get_curator_prompt())
    )

    # Stream of problems
    test_samples = [
        Sample(question="What is the capital of Japan?", ground_truth="Tokyo"),
        Sample(question="What is 7 × 8?", ground_truth="56"),
        Sample(question="Who wrote Romeo and Juliet?", ground_truth="Shakespeare"),
    ]

    environment = MathEnvironment()  # Works for general problems too

    print("\nProcessing samples in online mode...")

    # Run online adaptation
    results = adapter.run(test_samples, environment)

    # Display results for each sample
    for i, (sample, result) in enumerate(zip(test_samples, results), 1):
        print(f"\n--- Sample {i}: {sample.question}")
        print(f"Answer: {result.generator_output.final_answer}")
        print(f"Feedback: {result.environment_result.feedback}")
        print(f"Playbook size: {len(adapter.playbook.bullets())}")

        # Show confidence if available
        if hasattr(result.generator_output, 'raw') and 'answer_confidence' in result.generator_output.raw:
            confidence = result.generator_output.raw['answer_confidence']
            print(f"Confidence: {confidence:.2%}")


def demo_prompt_validation():
    """Demonstrate prompt output validation utilities."""
    print("\n" + "="*60)
    print("VALIDATION DEMO - Testing prompt output validation")
    print("="*60)

    # Example good generator output
    good_generator_output = json.dumps({
        "reasoning": "1. Analyzing the question. 2. Applying strategy. 3. Computing result.",
        "bullet_ids": ["bullet_001", "bullet_002"],
        "confidence_scores": {"bullet_001": 0.85, "bullet_002": 0.92},
        "final_answer": "42",
        "answer_confidence": 0.95
    })

    # Example bad generator output (missing required field)
    bad_generator_output = json.dumps({
        "reasoning": "Some reasoning",
        "bullet_ids": ["bullet_001"]
        # Missing "final_answer"
    })

    # Validate good output
    is_valid, errors = validate_prompt_output(good_generator_output, "generator")
    print(f"\nGood output validation: {'✓ PASSED' if is_valid else '✗ FAILED'}")
    if errors:
        print(f"Errors: {errors}")

    # Validate bad output
    is_valid, errors = validate_prompt_output(bad_generator_output, "generator")
    print(f"\nBad output validation: {'✓ PASSED' if is_valid else '✗ FAILED'}")
    if errors:
        print(f"Errors: {errors}")

    # Example reflector output with invalid tag
    bad_reflector_output = json.dumps({
        "reasoning": "Analysis complete",
        "error_identification": "none",
        "bullet_tags": [
            {"id": "bullet_001", "tag": "very_helpful"}  # Invalid tag
        ]
    })

    is_valid, errors = validate_prompt_output(bad_reflector_output, "reflector")
    print(f"\nBad reflector output: {'✓ PASSED' if is_valid else '✗ FAILED'}")
    if errors:
        print(f"Errors: {errors}")


def demo_custom_v2_prompt():
    """Demonstrate creating custom prompts based on v2 structure."""
    print("\n" + "="*60)
    print("CUSTOM PROMPT DEMO - Building on v2 structure")
    print("="*60)

    # Create a custom prompt for scientific reasoning
    custom_science_prompt = GENERATOR_V2_PROMPT.replace(
        "You are ACE Generator v2.0, an expert problem-solving agent.",
        "You are ACE Science Generator v1.0, specialized in scientific reasoning and hypothesis testing."
    ).replace(
        "Mode: Strategic Problem Solving",
        "Mode: Scientific Method Application"
    )

    # Add custom section
    custom_section = """
## Scientific Method Protocol

1. **Observation**: Identify key phenomena
2. **Hypothesis**: Form testable prediction
3. **Reasoning**: Apply scientific principles
4. **Conclusion**: Draw evidence-based answer

"""
    # Insert custom section
    custom_science_prompt = custom_science_prompt.replace(
        "## Core Responsibilities",
        custom_section + "## Core Responsibilities"
    )

    print("Created custom science prompt based on v2 structure")
    print("\nCustom sections added:")
    print("- Scientific Method Protocol")
    print("- Modified identity for science specialization")
    print("\nThis maintains v2 benefits while adding domain expertise")


def main():
    """Run all v2 prompt demonstrations."""
    print("\n" + "="*70)
    print(" "*20 + "ACE v2 PROMPTS DEMONSTRATION")
    print(" "*15 + "State-of-the-Art Prompt Engineering")
    print("="*70)

    # Run demos
    demo_math_prompts()
    demo_code_prompts()
    demo_online_learning_with_v2()
    demo_prompt_validation()
    demo_custom_v2_prompt()

    # Show available versions
    print("\n" + "="*60)
    print("AVAILABLE PROMPT VERSIONS")
    print("="*60)
    versions = PromptManager.list_available_versions()
    for role, available in versions.items():
        print(f"\n{role.capitalize()}:")
        for version in available:
            print(f"  - {version}")

    print("\n" + "="*60)
    print("v2 Prompts provide:")
    print("- Structured outputs with validation")
    print("- Domain-specific optimizations")
    print("- Confidence scoring")
    print("- Explicit anti-patterns")
    print("- Concrete examples")
    print("- Meta-cognitive awareness")
    print("="*60)


if __name__ == "__main__":
    main()