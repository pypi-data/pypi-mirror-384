import base64

from imagemcp.generator import (
    _detect_placeholder_prompt,
    _diagnose_no_image_response,
    _extract_images_from_message,
)


def _fake_png_payload(seed: bytes) -> str:
    return base64.b64encode(seed).decode("ascii")


def test_detect_placeholder_prompt_handles_known_templates() -> None:
    assert (
        _detect_placeholder_prompt("We still have TODO: fill prompt before launch")
        == "todo: fill prompt"
    )
    assert (
        _detect_placeholder_prompt("Reminder: TODO: update campaign objective this week")
        == "todo: update campaign objective"
    )
    assert _detect_placeholder_prompt("Create a vivid hero illustration") is None


def test_extract_images_from_message_with_legacy_images_array() -> None:
    payload = _fake_png_payload(b"legacy")
    message = {
        "images": [
            {
                "image_url": {
                    "url": f"data:image/png;base64,{payload}",
                    "mime_type": "image/png",
                }
            }
        ]
    }

    results = _extract_images_from_message(message)

    assert results == [
        {
            "data_url": f"data:image/png;base64,{payload}",
            "media_type": "image/png",
        }
    ]


def test_extract_images_from_message_with_output_image_blocks() -> None:
    payload = _fake_png_payload(b"gemini")
    message = {
        "content": [
            {
                "type": "output_image",
                "image_base64": payload,
                "mime_type": "image/png",
            }
        ]
    }

    results = _extract_images_from_message(message)

    assert len(results) == 1
    assert results[0]["media_type"] == "image/png"
    assert results[0]["data_url"].startswith("data:image/png;base64,")
    assert results[0]["data_url"].endswith(payload)


def test_extract_images_from_message_with_nested_tool_output() -> None:
    payload = _fake_png_payload(b"nested")
    message = {
        "content": [
            {
                "type": "tool_result",
                "output": [
                    {
                        "type": "output_image",
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": payload,
                        },
                    }
                ],
            }
        ]
    }

    results = _extract_images_from_message(message)

    assert len(results) == 1
    assert results[0]["media_type"] == "image/png"
    assert results[0]["data_url"].endswith(payload)


def test_diagnose_no_image_response_detects_content_policy() -> None:
    response = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": "I am unable to comply with that request due to policy restrictions.",
                },
            }
        ]
    }

    reason, detail, snippets = _diagnose_no_image_response(response)

    assert reason == "content_policy"
    assert detail is not None and "unable" in detail.lower()
    assert any("policy" in snippet.lower() for snippet in snippets)


def test_diagnose_no_image_response_text_response_without_refusal() -> None:
    response = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Here is a description of the concept without imagery.",
                        }
                    ]
                },
            }
        ]
    }

    reason, detail, snippets = _diagnose_no_image_response(response)

    assert reason == "provider_text_response"
    assert detail is not None and "description" in detail
    assert len(snippets) == 1
