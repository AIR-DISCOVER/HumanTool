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

### Story Writing Task Evaluation
The **CreativeWritingEvaluation** module provides tools for assessing the Human "Tool" framework's effectiveness in creative domains:
- Automated and human evaluation of narrative quality across dimensions like structure, character development, and originality
- Analysis of collaboration patterns between AI and human
- User experience assessment through standardized surveys (NASA-TLX, SUS)
- Scripts for quantitative and qualitative analysis of experimental data

### Travel Planning Task Evaluation
For evaluating the Travel Planning Task System, please refer to the evaluation protocols and metrics established in the original TravelPlanner benchmark paper:

```bibtex
@inproceedings{xie2024travelplanner,
  title={TravelPlanner: A Benchmark for Real-World Planning with Language Agents},
  author={Xie, Jian and Zhang, Kai and Chen, Jiangjie and Zhu, Tinghui and Lou, Renze and Tian, Yuandong and Xiao, Yanghua and Su, Yu},
  booktitle={Forty-first International Conference on Machine Learning},
  year={2024}
}
```

This includes evaluation criteria for planning quality, constraint satisfaction (environment, commonsense, and hard constraints), and overall task completion effectiveness as defined in the TravelPlanner framework.

## 📁 Code Structure

The repository is organized with separate modules for each task system.
```plaintext
/
├── 📂 StoryWritingTaskSystem/
│   ├── agent/
│   └── web_ui/
│
├── 📂 TravelPlanningTaskSystem/
│   ├── agent/
│   └── web_ui/
│
├── 📂 CreativeWritingEvaluation/
│   ├── analysis_scripts/
│   └── survey_materials/
│
├── 📂 common/
│
├── 📄 requirements.txt
└── 📄 README.md

Taking `StoryWritingTaskSystem/agent/` as an example, its internal structure might look like this:

/agent
├── 📂 core/
│   ├── 📄 agent.py
│   ├── 📄 prompts.py
│   └── 📄 nodes.py
│
├── 📂 tool/
│   ├── 📄 human.py
│   ├── 📄 llm.py
│   ├── 📄 writing.py
│   ├── 📄 travel_plan.py
│   └── 📄 tool_manager.py
│
├── 📂 utils/
│   ├── 📄 logger.py
│   └── 📄 json_parser.py
│
└── 📄 graph.py
```
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
    * Please refer to the specific README files for detailed instructions on each system:
    * For the Story Writing Task System: See [StoryWritingTaskSystem/README.md](StoryWritingTaskSystem/README.md)
    * For the Travel Planning Task System: [TravelPlanningTaskSystem/README.md](TravelPlanningTaskSystem/README.md)


## 📄 Citation

If you use this framework or code in your research, please cite our paper:

