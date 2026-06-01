"""
최초 실행 시 기본 계정 데이터를 생성합니다.
사용법: python init_data.py
"""
from database import SessionLocal, engine
import models
from auth import hash_password


def migrate():
    """기존 테이블에 신규 컬럼 추가 (없을 경우에만)"""
    with engine.connect() as conn:
        from sqlalchemy import text
        for col, col_type in [
            ("welfare_fee_rate", "FLOAT DEFAULT 0.0"),
            ("branch_total_amount", "FLOAT DEFAULT 0.0"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE settlements ADD COLUMN {col} {col_type}"))
                conn.commit()
                print(f"  [migrate] settlements.{col} 컬럼 추가")
            except Exception:
                conn.rollback()

    # SFSADMIN 비밀번호 업데이트
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.branch_code == "SFSADMIN").first()
    if user:
        user.password_hash = hash_password("Sfs!2024")
        db.commit()
        print("  [migrate] SFSADMIN 비밀번호 업데이트 완료")
    db.close()


def init():
    models.Base.metadata.create_all(bind=engine)
    migrate()
    db = SessionLocal()

    if db.query(models.User).count() > 0:
        print("이미 초기화되어 있습니다.")
        db.close()
        return

    # 지점 계정 (지점코드 + 비밀번호)
    branches = [
        ("SFS001", "Sfs001!2024", "서울목동지점", "서울"),
        ("SFS002", "Sfs002!2024", "인천송도지점", "인천"),
        ("SFS003", "Sfs003!2024", "대구지점", "대구"),
        ("SFS004", "Sfs004!2024", "광주지점", "광주"),
    ]

    for code, pw, name, region in branches:
        db.add(models.User(
            branch_code=code,
            password_hash=hash_password(pw),
            branch_name=name,
            region=region,
            role="branch",
        ))

    # SFS 관리자
    db.add(models.User(
        branch_code="SFSADMIN",
        password_hash=hash_password("Sfs!2024"),
        branch_name="삼성화재서비스",
        region="전국",
        role="coretail",
    ))

    db.commit()
    db.close()

    print("=" * 50)
    print("  데이터베이스 초기화 완료")
    print("=" * 50)
    print()
    print("[지점 담당자 계정]")
    for code, pw, name, _ in branches:
        print(f"  {code} / {pw}  ({name})")
    print()
    print("[SFS 관리자]")
    print("  SFSADMIN / Sfs!2024")
    print("=" * 50)


if __name__ == "__main__":
    init()
