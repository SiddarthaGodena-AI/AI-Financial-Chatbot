
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from google.cloud import storage
import pandas as pd
from io import BytesIO
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession

# Initialize Vertex AI
vertexai.init(project="project-name", location="us-central1")
model = GenerativeModel("gemini-1.5-flash-002")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust according to your requirements
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Option(BaseModel):
    id: int
    name: str

class Query(BaseModel):
    id: int  # ID of the selected option
    pan_id: Optional[str] = None  # User-provided PAN ID
    text: Optional[str] = None  # User-provided text for generative chat
    ipo_name: Optional[str] = None  # Name of the selected IPO
    lot_count: Optional[int] = None  # Number of lots user wants to buy

class Response(BaseModel):
    intent: str
    response: str
    options: List[Option]  # Options to be shown as buttons
    ipo_list: Optional[List[Dict[str, str]]] = None  # List of IPO data in dictionary form
    lot_details: Optional[Dict[str, str]] = None  # Details of the selected lot purchase

main_options = [
    {"id": 1, "name": "Bonds"},
    {"id": 2, "name": "Equity"},
    {"id": 3, "name": "IPO"},
]

sub_options = {
    1: [
        {"id": 4, "name": "Interests and Redemption"},
        {"id": 12, "name": "Connect to Human Operator"},
        {"id": 11, "name": "Back to Main Menu"},
    ],
    2: [
        {"id": 5, "name": "Dividends"},
        {"id": 12, "name": "Connect to Human Operator"},
        {"id": 11, "name": "Back to Main Menu"},
    ],
    3: [
        {"id": 6, "name": "Forthcoming IPO"},
        {"id": 7, "name": "Current IPO"},
        {"id": 8, "name": "Closed IPO"},
        {"id": 11, "name": "Back to Main Menu"},
    ],
}

bucket_name = "chatbot-funds"

def read_excel_from_gcs(bucket_name: str, blob_name: str):
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        file_content = blob.download_as_bytes()
        excel_data = BytesIO(file_content)
        df = pd.read_excel(excel_data)
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file {blob_name}: {str(e)}")

def format_ipo_data(ipo_data):
    ipo_list = []
    formatted_str = "Here are the IPO details:\n"
    for _, row in ipo_data.iterrows():
        ipo_entry = {
            "IPO Name": row['Name of IPO'],
            "Start Date": row['Start Date'].strftime("%Y-%m-%d"),
            "End Date": row['End Date'].strftime("%Y-%m-%d"),
            "Lot Size": str(row['Lot Size']),
            "Price Band": str(row['Price Band'])
        }
        ipo_list.append(ipo_entry)
        formatted_str += (
            f"- {row['Name of IPO']} (Start: {row['Start Date'].strftime('%Y-%m-%d')}, "
            f"End: {row['End Date'].strftime('%Y-%m-%d')}, "
            f"Lot Size: {row['Lot Size']}, Price Band: {row['Price Band']})\n"
        )
    return formatted_str, ipo_list

# Add this function to load the PAN data from the cloud storage
def read_pan_data_from_gcs(bucket_name: str, blob_name: str):
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        file_content = blob.download_as_bytes()
        excel_data = BytesIO(file_content)
        df = pd.read_excel(excel_data)
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file {blob_name}: {str(e)}")
    return not matching_rows.empty

def find_pan_in_data(pan_id: str, pan_data: pd.DataFrame):
    pan_data.columns = pan_data.columns.str.strip()
    if 'PAN-ID' not in pan_data.columns:
        raise HTTPException(status_code=500, detail="Column 'PAN-ID' not found in the PAN data.")
    matching_rows = pan_data[pan_data['PAN-ID'] == pan_id]
    return not matching_rows.empty

def get_chat_response(chat: ChatSession, user_input: str) -> str:
    try:
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in generating response: {str(e)}")

@app.post("/chat/", response_model=Response)
async def chat_with_user(query: Query):
    try:
        chat_session = model.start_chat()

        # Load PAN data from cloud storage (this is the missing step)
        pan_data = read_pan_data_from_gcs(bucket_name, "pan_data.xlsx")

        if query.text:
            ai_response = get_chat_response(chat_session, query.text)
            return Response(intent="Generative Chat", response=ai_response, options=[])

        if query.id == 0:
            response_text = "Please select an option:"
            return Response(intent="Main Menu", response=response_text, options=main_options)

        if query.id in [1, 2, 3]:
            category_name = next(option["name"] for option in main_options if option["id"] == query.id)
            response_text = f"You selected {category_name}. Please choose one of the following options:"
            return Response(intent=category_name, response=response_text, options=sub_options[query.id])

        if query.id in [6, 7, 8]:
            file_map = {
                6: "forthcoming_ipo.xlsx",
                7: "current_ipo.xlsx",
                8: "closed_ipo.xlsx",
            }
            file_name = file_map[query.id]

            ipo_data = read_excel_from_gcs(bucket_name, file_name)

            print(f"IPO Data for {file_name}: {ipo_data.head()}")

            response_text, ipo_list = format_ipo_data(ipo_data)

            if not ipo_list:
                response_text = "There are no IPOs available in this category."

            return Response(
                intent="IPO List",
                response=response_text,
                options=[],
                ipo_list=ipo_list
            )

        if query.id == 9:
            # Handle IPO name, PAN ID, lot name, and lot size collection
            if not query.ipo_name or not query.pan_id :
                response_text = "Please provide the IPO name, your PAN ID to continue."
                return Response(intent="Request All Details", response=response_text, options=[])

            # Validate PAN ID
            pan_valid = find_pan_in_data(query.pan_id, pan_data)
            if not pan_valid:
                return Response(
                    intent="Invalid PAN ID",
                    response="The provided PAN ID does not exist in our records.",
                    options=[]
                )

            # Validate IPO Name
            ipo_data = read_excel_from_gcs(bucket_name, "current_ipo.xlsx")
            selected_ipo = ipo_data[ipo_data['Name of IPO'] == query.ipo_name]

            if selected_ipo.empty:
                return Response(
                    intent="Invalid IPO Name",
                    response="The provided IPO name is not valid or does not exist.",
                    options=[]
                )

            price_band = selected_ipo["Price Band"].iloc[0]

            # Calculate price based on lot size
            if isinstance(price_band, str) and '₹' in price_band:
                # Remove the currency symbol and extra spaces
                price_band = price_band.replace('₹', '').strip()

                # If the price band contains a range (e.g., '₹70 - ₹100')
                if '-' in price_band:
                    price_band = sum(map(int, price_band.split('-'))) / 2  # Take the average of the range
                else:
                    price_band = int(price_band)  # Convert the cleaned price band to an integer


            # Handle lot size and lot count
            try:
                lot_count = int(query.lot_count)
                total_amount = lot_count * price_band
            except ValueError:
                return Response(
                    intent="Invalid Input",
                    response="Lot size and lot count must be valid numbers.",
                    options=[]
                )

            # Return the final amount calculation
            lot_details = {
                "IPO Name": query.ipo_name,
                "Number of Lots": str(lot_count),
                "Total Amount": str(total_amount)
            }

            return Response(
                intent="Lot Purchase Confirmation",
                response=f"Thank you for purchasing from {query.ipo_name}. You bought {lot_count}. Total cost: {total_amount}.",
                options=[{"id": 12, "name": "Back to Main Menu"}, {"id": 0, "name": "End Chat"}],
                lot_details=lot_details
            )

        if query.id == 12:
            response_text = "Returning to the main menu. Here are your options:"
            return Response(intent="Main Menu", response=response_text, options=main_options, ipo_list=[])

        response_text = "Invalid option selected."
        return Response(intent="Invalid", response=response_text, options=[], ipo_list=[])

    except Exception as e:
        print(f"Error: {str(e)}")  # Debugging log
        raise HTTPException(status_code=500, detail=str(e))

# API Root
@app.get("/")
async def root():
    return {"message": "Chatbot API is running successfully!"}