#!/usr/bin/env python3
"""
批量删除测试用户账号

用法:
    python scripts/delete_test_users.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# 加载环境变量（从 backend/.env）
backend_dir = Path(__file__).parent.parent / "backend"
env_file = backend_dir / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)
    # 将 Docker Compose 服务名替换为 localhost（本地运行）
    if "DATABASE_URL" in os.environ:
        os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"].replace("@mysql:", "@localhost:")
    if "REDIS_URL" in os.environ:
        os.environ["REDIS_URL"] = os.environ["REDIS_URL"].replace("redis://redis:", "redis://localhost:")
    if "CELERY_BROKER_URL" in os.environ:
        os.environ["CELERY_BROKER_URL"] = os.environ["CELERY_BROKER_URL"].replace("redis://redis:", "redis://localhost:")
    if "CELERY_RESULT_BACKEND" in os.environ:
        os.environ["CELERY_RESULT_BACKEND"] = os.environ["CELERY_RESULT_BACKEND"].replace("redis://redis:", "redis://localhost:")
else:
    # 如果没有 .env 文件，使用默认值（本地环境）
    os.environ.setdefault("DATABASE_URL", "mysql+pymysql://acm:acm_pass@localhost:3306/acm_bridge")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
    os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# 添加backend目录到Python路径
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.contest import ContestTeamRegistration
from app.models.member import Member
from app.models.submission import Submission
from app.models.team import Team, TeamMember
from app.models.user import User


def delete_user(user_id: int, db) -> bool:
    """删除单个用户及其关联数据"""
    user = db.get(User, user_id)
    if not user:
        print(f"  用户 ID {user_id} 不存在，跳过")
        return False

    print(f"  删除用户: {user.username} (ID: {user_id})")

    # 先获取该用户创建的团队列表（在删除成员关系之前）
    teams_created = db.execute(
        select(Team).where(Team.created_by_user_id == user_id)
    ).scalars().all()
    team_ids_created = [t.id for t in teams_created]

    # 删除该用户的团队成员关系
    team_members = db.execute(
        select(TeamMember).where(TeamMember.user_id == user_id)
    ).scalars().all()
    for tm in team_members:
        db.delete(tm)
    if team_members:
        print(f"    删除 {len(team_members)} 条团队成员关系")

    # 处理该用户创建的团队（删除成员关系后重新检查）
    for team_id in team_ids_created:
        team = db.get(Team, team_id)
        if not team:
            continue  # 团队可能已被删除
        
        # 检查团队是否还有其他成员（排除当前要删除的用户）
        other_members = db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id != user_id
            )
        ).scalars().all()
        
        # 过滤出用户仍然存在的成员
        valid_members = []
        for tm in other_members:
            member_user = db.get(User, tm.user_id)
            if member_user:
                valid_members.append(tm)
        
        if not valid_members:
            # 没有其他有效成员，先删除团队的竞赛报名记录，再删除团队
            contest_regs = db.execute(
                select(ContestTeamRegistration).where(ContestTeamRegistration.team_id == team_id)
            ).scalars().all()
            for reg in contest_regs:
                db.delete(reg)
            if contest_regs:
                print(f"    删除 {len(contest_regs)} 条竞赛报名记录")
            db.delete(team)
            print(f"    删除团队: {team.name} (ID: {team.id})")
        else:
            # 有其他有效成员，将created_by_user_id设为第一个有效成员的user_id
            team.created_by_user_id = valid_members[0].user_id
            print(f"    转移团队所有权: {team.name} (ID: {team.id}) -> 用户 ID {valid_members[0].user_id}")

    # 将该用户的提交记录的user_id设为NULL（保留提交记录，因为已经有member_id）
    submissions = db.execute(
        select(Submission).where(Submission.user_id == user_id)
    ).scalars().all()
    for submission in submissions:
        submission.user_id = None
    if submissions:
        print(f"    清空 {len(submissions)} 条提交记录的user_id")

    # 删除对应的Member记录（如果handle等于username，注册时自动创建的）
    member = db.execute(
        select(Member).where(Member.handle == user.username)
    ).scalars().first()
    if member:
        db.delete(member)
        print(f"    删除对应的Member记录: {member.handle} (ID: {member.id})")

    # 删除用户
    db.delete(user)
    return True


def main():
    # 要删除的测试用户ID列表
    test_user_ids = [
        4, 8, 9, 10, 11, 12, 13, 15, 16, 18, 19, 20, 21, 23, 24, 26, 27, 29, 30,
        31, 32, 33, 34, 35, 36, 37, 38, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51
    ]

    print(f"准备删除 {len(test_user_ids)} 个测试用户账号...")
    print()

    deleted_count = 0
    failed_count = 0

    for user_id in test_user_ids:
        db = SessionLocal()
        try:
            if delete_user(user_id, db):
                db.commit()
                deleted_count += 1
            else:
                db.rollback()
                failed_count += 1
            print()
        except Exception as e:
            db.rollback()
            print(f"  删除用户 ID {user_id} 时出错: {e}")
            failed_count += 1
            print()
        finally:
            db.close()

    print(f"完成！成功删除 {deleted_count} 个用户，失败 {failed_count} 个")


if __name__ == "__main__":
    main()
