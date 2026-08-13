def print_report(result):

    print("\n")
    print("=" * 50)
    print("       IELTS SPEAKING EVALUATION")
    print("=" * 50)

    print("\nFLUENCY & COHERENCE")
    print(
        "Band:",
        result["fluency_coherence"]["score"]
    )

    print(
        result["fluency_coherence"]["feedback"]
    )

    print("\nLEXICAL RESOURCE")
    print(
        "Band:",
        result["lexical_resource"]["score"]
    )

    print(
        result["lexical_resource"]["feedback"]
    )

    print("\nGRAMMATICAL RANGE & ACCURACY")
    print(
        "Band:",
        result["grammar"]["score"]
    )

    print(
        result["grammar"]["feedback"]
    )

    print("\nPRONUNCIATION")
    print(
        "Band:",
        result["pronunciation"]["score"]
    )

    print(
        result["pronunciation"]["feedback"]
    )

    print("\n" + "=" * 50)

    print(
        "OVERALL BAND:",
        result["overall"]["score"]
    )

    print("=" * 50)

    print("\nSUMMARY")
    print(
        result["overall"]["summary"]
    )

    print("\nRECOMMENDATIONS")

    for recommendation in result[
        "overall"
    ]["recommendations"]:

        print(
            "•",
            recommendation
        )
