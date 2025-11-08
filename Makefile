make.veo.docs:
	python extract_docs_llm.py docs/raw/gemini-video-gen-basics.html -o docs/veo-video-gen-basics.md
	
make.banana.docs:
	python extract_docs_llm.py docs/raw/gemini-imagen.html -o docs/gemini-imagegen-basics.md

make.veoguide.docs:
	python extract_docs_llm.py docs/raw/gemini-veo3-blog-workflow.html -o docs/veo-video-gen-workflow.md

docs: make.veo.docs make.banana.docs make.veoguide.docs