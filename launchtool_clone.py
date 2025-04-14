import streamlit as st
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address
from metadata_generator import create_metadata_json
from ipfs_helper import upload_to_ipfs
from base58 import b58decode

st.title("🪙 LaunchTool — Streamlit Cloud Final Fix")

client = Client("https://api.devnet.solana.com")

# --- Connect Wallet ---
st.subheader("Connect Wallet")
private_key_input = st.text_area("Enter your private key (base58 or array):", height=100)

if private_key_input:
    try:
        secret_key = bytes([int(x) for x in private_key_input.strip("[]").split(",")])
        keypair = Keypair.from_bytes(secret_key)
        st.success("Wallet connected (array format)")
    except ValueError:
        try:
            secret_key = b58decode(private_key_input.strip())
            keypair = Keypair.from_bytes(secret_key)
            st.success("Wallet connected (base58 format)")
        except Exception as e:
            st.error(f"Invalid private key format: {e}")
            st.stop()
else:
    st.warning("Paste your private key to continue.")
    st.stop()

pubkey = keypair.pubkey()

# --- Token Setup ---
st.subheader("Token Details")
name = st.text_input("Token Name")
symbol = st.text_input("Token Symbol")
supply = st.number_input("Total Supply", min_value=1, value=1000)
decimals = st.slider("Decimals", 0, 9, 2)
desc = st.text_area("Description")
website = st.text_input("Website (optional)")
logo = st.file_uploader("Token Logo (optional)", type=["png", "jpg", "jpeg"])

# --- Create Token ---
if st.button("Create Token"):
    if not name or not symbol:
        st.error("Please enter both a name and symbol.")
        st.stop()

    try:
        st.info("Creating token mint...")
        token_client = Token(
            conn=client,
            pubkey=None,  # will be created
            program_id=TOKEN_PROGRAM_ID,
            payer=keypair,
        )

        mint_pubkey = token_client.create_mint(
            mint_authority=pubkey,
            freeze_authority=pubkey,
            decimals=decimals
        )

        st.info("Creating ATA...")
        ata = token_client.create_associated_token_account(pubkey)

        st.info("Minting tokens...")
        amount = int(supply * 10**decimals)
        token_client.mint_to(
            dest=ata,
            mint_authority=keypair,
            amount=amount.to_solders(),
            signer_pubkey=pubkey
        )

        st.info("Uploading metadata...")
        metadata_json = create_metadata_json(name, symbol, desc, logo, website)
        metadata_uri = upload_to_ipfs(metadata_json)

        st.success("🎉 Token Created!")
        st.write("🧾 Mint Address:", mint_pubkey)
        st.write("🌐 Metadata URI:", metadata_uri)

    except Exception as e:
        st.error(f"An error occurred: {e}")
