import streamlit as st
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.system_program import create_account, CreateAccountParams
from solana.sysvar import SYSVAR_RENT_PUBKEY
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import initialize_mint, InitializeMintParams, get_associated_token_address, create_associated_token_account, mint_to, MintToParams
from metadata_generator import create_metadata_json
from ipfs_helper import upload_to_ipfs
from base58 import b58decode

st.title("🪙 LaunchTool — Final Streamlit Cloud-Compatible Version")

client = Client("https://api.devnet.solana.com")

# Connect Wallet
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

payer = keypair
payer_pubkey = payer.pubkey()

# Token Details
st.subheader("Token Details")
name = st.text_input("Token Name")
symbol = st.text_input("Token Symbol")
supply = st.number_input("Total Supply", min_value=1, value=1000)
decimals = st.slider("Decimals", 0, 9, 2)
desc = st.text_area("Description")
website = st.text_input("Website (optional)")
logo = st.file_uploader("Token Logo (optional)", type=["png", "jpg", "jpeg"])

if st.button("Create Token"):
    if not name or not symbol:
        st.error("Please enter both a name and symbol.")
        st.stop()

    try:
        st.info("Generating mint account...")

        mint_keypair = Keypair()
        mint_pubkey = mint_keypair.pubkey()

        min_balance_res = client.get_minimum_balance_for_rent_exemption(82)
        lamports = min_balance_res.value

        transaction = Transaction()

        transaction.add(
            create_account(
                CreateAccountParams(
                    from_pubkey=payer_pubkey,
                    new_account_pubkey=mint_pubkey,
                    lamports=lamports,
                    space=82,
                    program_id=TOKEN_PROGRAM_ID,
                )
            )
        )

        transaction.add(
            initialize_mint(
                InitializeMintParams(
                    program_id=TOKEN_PROGRAM_ID,
                    mint=mint_pubkey,
                    decimals=decimals,
                    mint_authority=payer_pubkey,
                    freeze_authority=payer_pubkey,
                )
            )
        )

        client.send_transaction(transaction, payer, mint_keypair)

        st.success(f"Mint created: {mint_pubkey}")

        # Create ATA
        ata = get_associated_token_address(payer_pubkey, mint_pubkey)
        tx = Transaction().add(
            create_associated_token_account(
                payer=payer_pubkey,
                owner=payer_pubkey,
                mint=mint_pubkey
            )
        )
        client.send_transaction(tx, payer)

        # Mint to ATA
        amount = int(supply * 10**decimals)
        tx = Transaction().add(
            mint_to(
                MintToParams(
                    program_id=TOKEN_PROGRAM_ID,
                    mint=mint_pubkey,
                    dest=ata,
                    authority=payer_pubkey,
                    amount=amount
                )
            )
        )
        client.send_transaction(tx, payer)

        st.info("Uploading metadata to IPFS...")
        metadata_json = create_metadata_json(name, symbol, desc, logo, website)
        metadata_uri = upload_to_ipfs(metadata_json)

        st.success("🎉 Token Created Successfully!")
        st.write("🧾 Mint Address:", mint_pubkey)
        st.write("🌐 Metadata URI:", metadata_uri)

    except Exception as e:
        st.error(f"An error occurred: {e}")
