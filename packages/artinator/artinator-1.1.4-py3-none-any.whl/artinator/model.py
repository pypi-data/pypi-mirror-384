import cli2
import json
import litellm
import os
import sys


class Model:
    def __init__(self):
        args, self.kwargs = self.configuration_parse(os.getenv(
            'MODEL',
            'openrouter/deepseek/deepseek-r1:free',  # some default model
        ).split())
        self.name = args[0]

    @staticmethod
    def configuration_parse(tokens):
        # convert "a bar=1" string into args=['a'] kwargs={'b': 1}
        args = list()
        kwargs = dict()
        for token in tokens:
            key = None
            if '=' in token:
                key, value = token.split('=')
            else:
                value = token

            try:
                value = float(value)
            except ValueError:
                try:
                    value = int(value)
                except ValueError:
                    pass

            if key:
                kwargs[key] = value
            else:
                args.append(value)
        return args, kwargs

    async def send(self, context):
        if os.getenv('LITELLM_DEBUG'):
            litellm._turn_on_debug()
        tokens = litellm.token_counter(model=self.name, messages=context.messages)
        print('tokens', tokens)
        input_cost = litellm.completion_cost(
            model=self.name,
            messages=context.messages,
        )
        print('cost', input_cost)

        kwargs = dict()
        if litellm.supports_function_calling(self.name):
            kwargs['tools'] = context.tools
            messages = context.messages
        else:
            cli2.log.warn(f'Emulating tool calling on {self.name}')
            litellm.add_function_to_prompt = True
            kwargs['functions_unsupported_model'] = context.tools
            messages = [
                message if message['role'] != 'tool' else dict(
                    role='user',
                    content=message['content'],
                )
                for message in context.messages
            ]

        stream = await litellm.acompletion(
            messages=messages,
            stream=True,
            model=self.name,
            **kwargs,
            **self.kwargs,
        )

        full_content = ''
        printed_lines = 0
        full_reasoning = ''
        reasoning_printed = False
        code_open = False
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
            if hasattr(chunk, 'choices') and chunk.choices:
                delta = chunk.choices[0].delta
                if reasoning := getattr(delta, 'reasoning_content', None):
                    if stream:
                        if not reasoning_printed:
                            print(cli2.t.o.b('REASONING'), file=sys.stderr)
                            reasoning_printed = True
                        print(
                            cli2.t.G(delta.reasoning_content),
                            end='',
                            flush=True,
                            file=sys.stderr,
                        )
                    full_reasoning += reasoning

                if content := getattr(delta, 'content', ''):
                    if reasoning_printed:
                        # separate reasoning output visually
                        print('\n', file=sys.stderr)
                        reasoning_printed = False

                    full_content += content
                    if not content.endswith('\n'):
                        continue

                    new_lines = full_content.split('\n')[printed_lines:]
                    for new_line in new_lines:
                        if new_line.strip().startswith('```'):
                            code_open = not code_open

                    if not new_lines:
                        continue

                    highlight_content = full_content
                    if code_open:
                        # manuall close code block for pygments to highlight
                        if not highlight_content.endswith('\n'):
                            highlight_content += '\n'
                        highlight_content += '```'

                    highlighted = cli2.highlight(highlight_content, 'Markdown')
                    highlighted_lines = highlighted.split('\n')

                    if code_open:
                        highlighted_lines = highlighted_lines[:-1]

                    print(
                        '\n'.join(highlighted_lines[printed_lines:]),
                        flush=True,
                        file=sys.stderr,
                    )
                    printed_lines = len(highlighted_lines)

        new_lines = full_content.split('\n')[printed_lines:]
        for new_line in new_lines:
            if new_line.strip().startswith('```'):
                code_open = not code_open

        highlight_content = full_content
        if code_open:
            # manuall close code block for pygments to highlight code
            if not highlight_content.endswith('\n'):
                highlight_content += '\n'
            highlight_content += '```'

        highlighted = cli2.highlight(highlight_content, 'Markdown')
        highlighted_lines = highlighted.split('\n')

        if code_open:
            highlighted_lines = highlighted_lines[:-1]

        print(
            '\n'.join(highlighted_lines[printed_lines:]),
            flush=True,
            file=sys.stderr,
        )

        text = full_content or full_reasoning
        print('cost', stream._hidden_params["response_cost"])
        context.messages.append({
            'role': 'assistant',
            'content': text,
        })
        response = litellm.stream_chunk_builder(chunks)

        if litellm.add_function_to_prompt and text.strip().startswith('{'):
            # finish tool call emulation
            try:
                call = json.loads(text)
            except:
                cli2.log.error(f'could not json parse {text}')
            else:
                try:
                    response.choices[0].message.tool_calls = [
                        litellm.ChatCompletionMessageToolCall(
                            function=litellm.Function(
                                name=call['name'],
                                arguments=json.dumps(call['arguments']),
                            ),
                        )
                    ]
                except:
                    cli2.log.error(f'call emulation failed with {text}')
                else:
                    text = ''

        breakpoint()
        return text, response
