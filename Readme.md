Stella – AI Agent for Testing

Description

Stella is an open-source platform that provides AI agents with unique personalities to test and review your app. These virtual testers deliver immediate, unbiased feedback on your digital products, making beta testing more accessible, efficient, and scalable.

Features

24/7 Testing Availability: Receive instant feedback whenever you need it.
Diverse Persona Library: Test your app with a variety of virtual testers offering unique perspectives.
Detailed Analytics: Gain comprehensive insights into UX/UI and user behavior.
Automated Reporting: Generate structured and actionable feedback reports.
API Integration: Seamlessly integrate Stella into your development workflow.
Workflow


**Flow:**
[Workflow]("images/flow.png")

<img src="images/flow.png" alt="Image description" width="999">

Installation

Follow these steps to install Stella:

Create and activate a virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
Clone the repository:
git clone https://github.com/seifbenayed/stella.git
cd stella
Install the required packages:
pip install -r requirements.txt

Configuration

Update the .env file located at the root of the project with the following variables:

Persona ID: Choose the persona ID from MongoDB:
persona=your_persona_object_id  # See the list below
AI Model Key: Add your API key for the AI model (supports gpt-4o, o1, o1-mini, or sonnet-3-5).
AI Model Identifier: Specify your chosen model:
llm_id=your_chosen_model
Preconfigured Personas
Stella comes with seven preconfigured personas, each representing a different user segment:

Damien: A status-driven CEO focused on premium experiences. ( ID=672943da00e68f541d8a4e46)
Vincent: A growth-oriented entrepreneur prioritizing ROI. ID=6729448500e68f541d8a4e49
Sarah: A millennial financial planner emphasizing mobile usage. ID=6729448500e68f541d8a4e4a
Selma: An eco-conscious future parent who values sustainability. ID=6729452e00e68f541d8a4e4b
Laure: A beauty-tech enthusiast on the lookout for trends. ID=6729452e00e68f541d8a4e4c
Amir: An analytical, intellectually driven entrepreneur. ID = 6729464e00e68f541d8a4e4d
Lina: A Gen Z digital native who values social proof. ID=6729464e00e68f541d8a4e4e
Contributing

We welcome contributions! To get started:

Fork the project.
Create a feature branch:
git checkout -b feature/AmazingFeature
Commit your changes:
git commit -m "Add AmazingFeature"
Push your branch:
git push origin feature/AmazingFeature
Open a Pull Request.
For more details, please refer to our Contributing Guide.

Requirements

Python >= 3.9
MongoDB >= 4.4
Acknowledgments

Stella leverages several key technologies:

LangChain for AI agent creation
Playwright for web interaction
MongoDB for persona management
Various AI models for intelligent analysis
Support

📝 Documentation
🐛 Issue Tracker
💬 Community Forum
License

This project is licensed under the Apache 2.0 License – see the LICENSE file for details.

Special Thanks

A heartfelt thank you to all the contributors who have helped shape Stella's virtual testing capabilities.



