# HumanTool: An AI-led Human-AI Collaboration Framework

This repository contains the official implementation for the research paper: **"Human 'Tool': Reconstructing Human-AI Collaboration Framework in the Superintelligence Epoch."**

This project proposes and implements a novel paradigm for human-AI collaboration called **Human "Tool"**.


## 💡 Core Concept

Traditional human-AI collaboration models often place the human in a leadership role, responsible for directing the AI, delegating tasks, and validating results. However, when the AI's capabilities surpass the human's, this model can turn the human into a bottleneck, reducing overall efficiency.

Our **Human "Tool"** framework inverts this dynamic. We advocate for an **AI-led, proactive** collaboration model. In this framework, the AI acts as the "project manager," responsible for planning, coordinating, and driving the entire workflow. The human, in turn, acts as a callable "expert tool," who is proactively invoked by the AI at critical moments that require uniquely human skills like creativity, ethical judgment, empathy, or complex contextual awareness.



This framework is realized through three key mechanisms:

1.  **Modeling Human Tools**: Defining human expertise, available information, and authority as "tools" that the AI can understand and invoke.
2.  **Dynamic Invocation**: The AI intelligently determines when to "call" the human tool based on the current task's needs and its own limitations.
3.  **Efficient Communication**: Establishing natural and effective communication protocols that allow the AI to clearly request input from the human and seamlessly integrate the feedback.


## 💻 About this Repository

This repository contains the two core experimental systems used in the paper to validate the effectiveness of the **Human "Tool"** framework:

* ✍️ **Story Writing Task System**: An example of a **creative task**. The AI manages the overall story structure and progression, calling upon the human for inspiration on plot twists, character development, and other creative elements.
* ✈️ **Travel Planning Task System**: An example of a **decision-optimization task**. The AI handles the search and comparison of vast amounts of flight and hotel data using dedicated planning tools, seeking human input when it's time to weigh personal preferences and make final decisions. The system follows a structured workflow with clear task decomposition and user participation markers.

## 📊 Evaluation

The **CreativeWritingEvaluation** module provides tools for assessing the Human "Tool" framework's effectiveness in creative domains:

Automated and human evaluation of narrative quality across dimensions like structure, character development, and originality
Analysis of collaboration patterns between AI and human
User experience assessment through standardized surveys (NASA-TLX, SUS)
Scripts for quantitative and qualitative analysis of experimental data


## 📁 Code Structure

The repository is organized with separate modules for each task system.

Of course. Here is the content for your README.md file, written in English.

You can copy the text below and save it as a file named README.md.

Markdown

# HumanTool: An AI-led Human-AI Collaboration Framework

This repository contains the official implementation for the research paper: **"Human 'Tool': Reconstructing Human-AI Collaboration Framework in the Superintelligence Epoch."**

This project proposes and implements a novel paradigm for human-AI collaboration called **Human "Tool"**.


## 💡 Core Concept

Traditional human-AI collaboration models often place the human in a leadership role, responsible for directing the AI, delegating tasks, and validating results. However, when the AI's capabilities surpass the human's, this model can turn the human into a bottleneck, reducing overall efficiency.

Our **Human "Tool"** framework inverts this dynamic. We advocate for an **AI-led, proactive** collaboration model. In this framework, the AI acts as the "project manager," responsible for planning, coordinating, and driving the entire workflow. The human, in turn, acts as a callable "expert tool," who is proactively invoked by the AI at critical moments that require uniquely human skills like creativity, ethical judgment, empathy, or complex contextual awareness.



This framework is realized through three key mechanisms:

1.  **Modeling Human Tools**: Defining human expertise, available information, and authority as "tools" that the AI can understand and invoke.
2.  **Dynamic Invocation**: The AI intelligently determines when to "call" the human tool based on the current task's needs and its own limitations.
3.  **Efficient Communication**: Establishing natural and effective communication protocols that allow the AI to clearly request input from the human and seamlessly integrate the feedback.


## 💻 About this Repository

This repository contains the two core experimental systems used in the paper to validate the effectiveness of the **Human "Tool"** framework:

* ✍️ **Story Writing Task System**: An example of a **creative task**. The AI manages the overall story structure and progression, calling upon the human for inspiration on plot twists, character development, and other creative elements.
* ✈️ **Travel Planning Task System**: An example of a **decision-optimization task**. The AI handles the search and comparison of vast amounts of flight and hotel data, seeking human input when it's time to weigh personal preferences and make final decisions.


## 📁 Code Structure

The repository is organized with separate modules for each task system.

/
├── StoryWritingTaskSystem/      # The story writing task system
│   ├── agent/                   # Core agent logic
│   └── web_ui/                  # Frontend user interface
│
├── TravelPlanningTaskSystem/    # The travel planning task system
│   ├── agent/                   # Core agent logic
│   └── web_ui/                  # Frontend user interface
│
├── CreativeWritingEvaluation/   # Story Writing Evaluation System & User Study
│   ├── analysis_scripts/        # Scripts for analyzing experimental data (Python/R)
│   └── survey_materials/        # Survey materials (e.g., NASA-TLX, SUS)
│
├── common/                      # Shared modules or utilities
│
├── requirements.txt             # Project dependencies
└── README.md                    # This file

Taking `StoryWritingTaskSystem/agent/` as an example, its internal structure might look like this:

/agent
├── core/                        # Core system components
│   ├── agent.py                 # Main agent logic and initialization
│   ├── prompts.py               # System prompts defining agent behavior and structure
│   └── nodes.py                 # Workflow node management
│
├── tool/                        # Tool implementations
│   ├── human.py                 # Human tool modeling and interaction logic
│   ├── llm.py                   # LLM-based tools (KnowledgeAnalyzer, Thinking, General)
│   ├── writing.py               # Creative writing tools (for story system)
│   ├── travel_plan.py           # Travel-specific planning tools
│   └── tool_manager.py          # Tool management and caching
│
├── utils/                       # Utility modules
│   ├── logger.py                # Logging functionality
│   └── json_parser.py           # JSON parsing and validation
│
└── graph.py                     # Workflow graph definition and executio

## 🚀 Getting Started

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/AIR-DISCOVER/HumanTool.git](https://github.com/AIR-DISCOVER/HumanTool.git)
    cd HumanTool
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your API keys:**
    * Create a `.env` file in the root directory.
    * Add your Large Language Model API key to the file: `LLM_API_KEY='your-api-key-here'`

4.  **Run a system:**
    ```bash
    # Navigate to the desired system and run the main script
    cd StoryWritingTaskSystem/
    python agent/main.py
    ```


## 📄 Citation

If you use this framework or code in your research, please cite our paper:

