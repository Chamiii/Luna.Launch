
import streamlit as st
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction
from solders.message import Message
from solders.transaction import Transaction
from solders.system_program import create_account, CreateAccountParams
from solana.rpc.api import Client
from spl.token.instructions import (
    create_associated_token_account,
    mint_to,
    MintToParams,
    initialize_mint,
    InitializeMintParams
)
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from base58 import b58decode

st.title("🪙 Solana Token Creator — FINAL WORKING COPY")

client = Client("https://api.devnet.solana.com")

st.subheader("Connect Wallet")
private_key_input = st.text_area("Enter your private key (base58 or array):", height=100)

if private_key_input:
    try:
        secret_key = bytes([int(x) for x in private_key_input.strip("[]").split(",")])
        payer = Keypair.from_bytes(secret_key)
        st.success("Wallet connected (array format)")
    except ValueError:
        try:
            secret_key = b58decode(private_key_input.strip())
            payer = Keypair.from_bytes(secret_key)
            st.success("Wallet connected (base58 format)")
        except Exception as e:
            st.error(f"Invalid private key format: {e}")
            st.stop()
else:
    st.warning("Paste your private key to continue.")
    st.stop()

payer_pubkey = payer.pubkey()

st.subheader("Token Details")
name = st.text_input("Token Name")
symbol = st.text_input("Token Symbol")
supply = st.number_input("Total Supply", min_value=1, value=1000)
decimals = st.slider("Decimals", 0, 9, 2)

if st.button("Create Token"):
    try:
        mint = Keypair()
        mint_pubkey = mint.pubkey()

        rent = client.get_minimum_balance_for_rent_exemption(82).value
        ata = Pubkey.find_program_address(
            [bytes(payer_pubkey), bytes(TOKEN_PROGRAM_ID), bytes(mint_pubkey)],
            ASSOCIATED_TOKEN_PROGRAM_ID
        )[0]

        instructions = []

        instructions.append(
            create_account(
                CreateAccountParams(
                    from_pubkey=payer_pubkey,
                    to_pubkey=mint_pubkey,
                    lamports=rent,
                    space=82,
                    owner=TOKEN_PROGRAM_ID
                )
            )
        )

        instructions.append(
            initialize_mint(
                InitializeMintParams(
                    program_id=TOKEN_PROGRAM_ID,
                    mint=mint_pubkey,
                    decimals=decimals,
                    mint_authority=payer_pubkey,
                    freeze_authority=payer_pubkey
                )
            )
        )

        instructions.append(
            create_associated_token_account(
                payer=payer_pubkey,
                owner=payer_pubkey,
                mint=mint_pubkey
            )
        )

        amount = supply * (10 ** decimals)
        instructions.append(
            mint_to(
                MintToParams(
                    program_id=TOKEN_PROGRAM_ID,
                    mint=mint_pubkey,
                    dest=ata,
                    authority=payer,
                    amount=amount
                )
            )
        )

        message = Message(instructions=instructions, payer=payer_pubkey)
        tx = Transaction(message=message, signatures=[])
        tx.sign([payer, mint])
        client.send_transaction(tx, payer, mint)

        st.success("🎉 Token created and minted successfully!")
        st.write("🧾 Mint Address:", str(mint_pubkey))
        st.write("🔗 [View on Solana Explorer](https://explorer.solana.com/address/" + str(mint_pubkey) + "?cluster=devnet)")

    except Exception as e:
        st.error(f"An error occurred: {e}")
