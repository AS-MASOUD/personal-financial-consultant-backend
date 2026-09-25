import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.core.exceptions import EntityNotFoundException
from src.app.database.models import AIConversationModel, AIMessageModel
from src.modules.ai.application.dtos import (
    ChatMessageRequest,
    MessageResponse,
)
from src.modules.ai.domain.interfaces import IAIProvider
from src.modules.ai.infrastructure.mock_provider import MockAIProvider
from src.modules.analytics.application.services import AnalyticsService


class AIService:
    def __init__(self, db: AsyncSession, provider: IAIProvider | None = None):
        self.db = db
        self.provider = provider or MockAIProvider()

    async def list_conversations(self) -> list[AIConversationModel]:
        stmt = select(AIConversationModel).order_by(AIConversationModel.updated_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_conversation(self, conversation_id: uuid.UUID) -> AIConversationModel:
        stmt = (
            select(AIConversationModel)
            .options(selectinload(AIConversationModel.messages))
            .where(AIConversationModel.id == conversation_id)
        )
        result = await self.db.execute(stmt)
        convo = result.scalar_one_or_none()
        if not convo:
            raise EntityNotFoundException("AIConversation", conversation_id)
        return convo

    async def process_chat(self, payload: ChatMessageRequest) -> MessageResponse:
        # 1. Get or create conversation
        if payload.conversation_id:
            convo = await self.get_conversation(payload.conversation_id)
        else:
            title = payload.content[:40] + ("..." if len(payload.content) > 40 else "")
            convo = AIConversationModel(title=title)
            self.db.add(convo)
            await self.db.flush()
            await self.db.refresh(convo)

        # 2. Add user message
        user_msg = AIMessageModel(
            conversation_id=convo.id,
            role="user",
            content=payload.content,
        )
        self.db.add(user_msg)

        # 3. Controlled Deterministic Tool Invocation: get live financial overview
        analytics = AnalyticsService(self.db)
        overview = await analytics.get_overview()

        tool_data = {
            "net_worth": str(overview.net_worth),
            "total_assets": str(overview.total_assets),
            "total_liabilities": str(overview.total_liabilities),
            "liquid_cash": str(overview.liquid_cash),
            "monthly_income": str(overview.monthly_income),
            "monthly_expenses": str(overview.monthly_expenses),
            "monthly_debt_service": str(overview.monthly_debt_service),
            "monthly_free_cashflow": str(overview.monthly_free_cashflow),
            "asset_allocation": overview.asset_allocation,
            "liability_breakdown": overview.liability_breakdown,
        }

        # 4. Synthesize AI response using deterministic data
        assistant_content = await self.provider.generate_response(
            messages=[{"role": "user", "content": payload.content}],
            tools_context=tool_data,
        )

        assistant_msg = AIMessageModel(
            conversation_id=convo.id,
            role="assistant",
            content=assistant_content,
            tool_calls={"invocations": ["get_financial_overview"]},
            tool_results=tool_data,
        )
        self.db.add(assistant_msg)
        await self.db.flush()
        await self.db.refresh(assistant_msg)

        return MessageResponse(
            id=assistant_msg.id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            tool_calls=assistant_msg.tool_calls,
            tool_results=assistant_msg.tool_results,
            created_at=assistant_msg.created_at,
        )
