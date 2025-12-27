# univCabi - Backend

대학 사물함(캐비닛) 대여 관리 시스템의 백엔드 서버입니다. Django 프레임워크를 기반으로 Clean Architecture 원칙을 적용하고, Celery + Redis + Kafka를 활용한 대규모 트래픽 처리 및 블록체인 기반 이력 관리 기능을 제공합니다.

## Backend Architecture Structure

본 프로젝트의 백엔드는 복잡한 비즈니스 로직을 효율적으로 처리하고, 유지보수성과 확장성을 확보하기 위해 다음과 같은 아키텍처 설계를 적용했습니다.

### Key Architectural Concepts

#### Django-Based Layered Architecture

Django 프레임워크의 강점(ORM, Admin, Middleware)을 유지하면서도 Clean Architecture 원칙을 적용하여 비즈니스 로직을 프레임워크로부터 분리했습니다.

```mermaid
graph TD
    subgraph Presentation ["Presentation Layer"]
        Views["API Views (DRF)"]
        Serializers["Serializers"]
        DTOs["Request DTOs"]
        Middleware["Middleware (JWT, CORS)"]
    end

    subgraph Business ["Business Logic Layer"]
        CabinetService["Cabinet Service"]
        BlockchainService["Blockchain Service"]
        HistoryService["History Service"]
        BookmarkService["Bookmark Service"]
    end

    subgraph Persistence ["Persistence Layer"]
        Repository["Repository Pattern"]
        Models["Django Models (ORM)"]
    end

    subgraph Infrastructure ["Infrastructure Layer"]
        Celery["Celery Tasks"]
        Redis["Redis Cache & Lock"]
        Kafka["Kafka Producer/Consumer"]
        ThreadPool["Custom Thread Pool"]
        Blockchain["Web3 Provider"]
    end

    subgraph Database
        DB[("PostgreSQL / SQLite")]
        RedisDB[("Redis")]
        ETH[("Ethereum Sepolia")]
    end

    %% Flow
    Views --> DTOs
    Views --> Business
    Business --> Repository
    Repository --> Models
    Models --> DB

    Business --> Infrastructure
    Celery --> RedisDB
    Redis --> RedisDB
    Kafka --> Business
    Blockchain --> ETH
```

#### Triple-Redundancy Async Processing Architecture

대규모 트래픽 처리를 위해 **3단계 병렬 처리 아키텍처**를 구현했습니다:

```mermaid
sequenceDiagram
    participant Client
    participant API as Django API
    participant TP as Thread Pool
    participant Celery
    participant Kafka
    participant Redis
    participant DB as Database

    Client->>API: POST /cabinet/rent

    par Primary Processing
        API->>TP: Submit to Thread Pool
        TP->>Redis: Acquire Distributed Lock
        Redis-->>TP: Lock Acquired
        TP->>DB: Process Rental
        TP->>Redis: Store Result
    and Secondary Processing
        API->>Celery: Enqueue Task
        Celery->>Redis: Acquire Lock
        Celery->>DB: Process Rental (if needed)
    and Tertiary Processing
        API->>Kafka: Publish Event
        Kafka->>Kafka: Consumer Group Listens
        Kafka->>DB: Process Rental (if needed)
    end

    API->>Redis: Poll for Result
    Redis-->>API: Return Result
    API-->>Client: Response
```

**각 계층의 역할:**

1. **Thread Pool (Primary)** - 가장 빠른 응답 속도

   - 애플리케이션 내부 스레드 풀 (5 workers)
   - 즉각적인 처리로 평균 응답시간 최소화
   - 경량 작업에 최적화

2. **Celery (Secondary)** - 안정성과 확장성

   - Redis 기반 분산 작업 큐
   - Thread Pool 과부하 시 자동 처리
   - 재시도 로직 및 작업 스케줄링

3. **Kafka (Tertiary)** - 장애 복구 및 이벤트 스트리밍
   - 메시지 영속성 보장
   - Consumer Group을 통한 수평 확장
   - 시스템 장애 시에도 이벤트 손실 방지

#### Distributed Locking Strategy

Redis를 활용한 분산 락으로 동시성 문제를 해결했습니다:

```mermaid
graph LR
    subgraph Users
        U1[User A]
        U2[User B]
        U3[User C]
    end

    subgraph RedisLock [Redis Distributed Lock]
        Lock["cabinet:123:rent
        (UUID: abc-def-123)
        TTL: 30s"]
    end

    subgraph Processing
        Winner[User A Processing]
        Queue[Users B & C Waiting]
    end

    U1 -->|Acquire Lock ✓| Lock
    U2 -->|Try Lock ✗| Lock
    U3 -->|Try Lock ✗| Lock

    Lock -->|Lock Acquired| Winner
    Lock -.->|Blocked| Queue

    Winner -->|Release Lock| Lock
    Queue -->|Next User Acquires| Lock
```

**구현 특징:**

- UUID 기반 소유권 검증
- 자동 TTL로 데드락 방지
- 사물함별 독립적인 락 (세밀한 동시성 제어)

#### Blockchain-Based Audit Trail

블록체인(Ethereum)을 활용한 변조 불가능한 대여 이력 관리:

```mermaid
graph TD
    subgraph DjangoBackend [Django Backend]
        Rental[Cabinet Rental Event]
        History[Create cabinet_histories record]
    end

    subgraph BlockchainService [Blockchain Service]
        Web3[Web3.py Provider]
        Mint[Mint NFT Function]
    end

    subgraph EthereumNetwork [Ethereum Sepolia Testnet]
        Contract[CabinetHistoryNFT.sol
        ERC-721 Contract]
        NFT[NFT Token
        TokenId = history.id]
    end

    subgraph NFTMetadata [NFT Metadata]
        Data["cabinetId: 123
        historyId: 456
        userAddress: 0x...
        rentedAt: timestamp
        expiredAt: timestamp"]
    end

    Rental --> History
    History --> Mint
    Mint --> Web3
    Web3 --> Contract
    Contract --> NFT
    NFT --> Data
```

**활용 사례:**

- 학생의 사물함 사용 이력을 블록체인에 영구 기록
- 대여/반납 시점의 변조 방지
- 투명한 관리 기록 및 감사 추적
- NFT 기반 디지털 증명서 발급

## Traffic Handling Strategy

### 고성능 처리 기법

#### Redis 기반 즐겨찾기 버퍼링

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Redis
    participant CeleryBeat
    participant DB

    User->>API: POST /cabinet/bookmark/add
    API->>Redis: SADD bookmarks:{user_id} {cabinet_id}
    Redis-->>API: OK (1-2ms)
    API-->>User: Success (즉시 응답)

    Note over CeleryBeat: Every 5 seconds
    CeleryBeat->>Redis: SMEMBERS bookmarks:*
    Redis-->>CeleryBeat: Return all bookmarks
    CeleryBeat->>DB: Bulk INSERT/UPDATE
    DB-->>CeleryBeat: Committed
```

#### 동시성 제어를 통한 데이터 정합성

**시나리오**: 100000명의 사용자가 동시에 같은 사물함 대여 시도

```mermaid
graph TD
    U1[User 1] -->|Try Lock| Lock[Redis Lock: cabinet:123]
    U2[User 2] -->|Try Lock| Lock
    U3[User 3...100000] -->|Try Lock| Lock

    Lock -->|Acquired| U1
    Lock -.->|Blocked| U2
    Lock -.->|Blocked| U3

    U1 -->|Process Rental| DB[(Database)]
    U1 -->|Release Lock| Lock

    Lock -->|Next Acquire| U2
    U2 -.->|Already Rented Error| U2
```

---

## Database Schema

### ERD (Entity Relationship Diagram)

```mermaid
erDiagram
    authns ||--|| users : "OneToOne"
    buildings ||--o{ cabinets : "has many"
    buildings ||--o{ users : "preferred by"
    users ||--o{ cabinets : "currently renting"
    users ||--o{ cabinet_histories : "rental history"
    users ||--o{ cabinet_bookmarks : "bookmarks"
    cabinets ||--|| cabinet_positions : "has position"
    cabinets ||--o{ cabinet_histories : "history"
    cabinets ||--o{ cabinet_bookmarks : "bookmarked by"

    authns {
        bigint id PK
        string student_number UK "학번"
        string password "해시된 비밀번호"
        string role "NORMAL/ADMIN"
        datetime created_at
        datetime updated_at
    }

    users {
        bigint id PK
        string name "사용자 이름"
        string affiliation "소속"
        string phone_number "연락처"
        bigint building_id FK "선호 건물"
        boolean is_visible "공개 여부"
        datetime created_at
        datetime updated_at
    }

    buildings {
        bigint id PK
        string name "건물명 (Enum)"
        int floor "층수"
        string section "구역"
        int width "사물함 배치 가로"
        int height "사물함 배치 세로"
    }

    cabinets {
        bigint id PK
        string cabinet_number "사물함 번호"
        string status "AVAILABLE/USING/BROKEN/OVERDUE"
        bigint user_id FK "현재 사용자"
        bigint building_id FK "소속 건물"
        boolean payable "유료 여부"
        string reason "사용 불가 사유"
        datetime created_at
        datetime updated_at
    }

    cabinet_positions {
        bigint id PK
        bigint cabinet_id FK "사물함"
        int cabinet_x_pos "X 좌표"
        int cabinet_y_pos "Y 좌표"
    }

    cabinet_histories {
        bigint id PK
        bigint user_id FK "대여자"
        bigint cabinet_id FK "사물함"
        datetime created_at "대여 시작일"
        datetime expired_at "만료 예정일"
        datetime ended_at "실제 반납일"
    }

    cabinet_bookmarks {
        bigint id PK
        bigint user_id FK "사용자"
        bigint cabinet_id FK "사물함"
        boolean is_deleted "삭제 여부"
        datetime created_at
        datetime updated_at
    }
```

---

## Technology Stack

### Backend Framework

- **Django**: 5.2.1
- **Django REST Framework**: 3.15.2
- **Python**: 3.10+

### Authentication

- **djangorestframework-simplejwt**: 5.4.0

### Database

- **Development**: SQLite3
- **Production**: PostgreSQL (지원)
- **ORM**: Django ORM

### Caching & Message Queue

- **Redis**: 5.2.1
- **django-redis**: 5.4.0
- **Celery**: 5.5.2
- **kafka-python**: 2.1.5

### Blockchain

- **Web3.py**: 7.11.0
- **Solidity**: ^0.8.0
- **Network**: Ethereum Sepolia Testnet
- **Provider**: Infura

### API Documentation

- **drf-yasg**: 1.21.8 (Swagger/OpenAPI)

### Development Tools

- **django-environ**: 0.11.2 (환경 변수 관리)
- **django-cors-headers**: 4.6.0 (CORS)

---

## 🧑🏻‍💻 프로젝트 멤버

|  이름  | 역할                          | GitHub                                      |
| :----: | :---------------------------- | :------------------------------------------ |
| 민영재 | PM, Backend, Frontend, Design | [yeomin4242](https://github.com/yeomin4242) |
| 민웅기 | Backend, Frontend, Design     | [minwoonggi](https://github.com/minwoonggi) |
| 김주희 | Frontend, Design              | [joooii](https://github.com/joooii)         |
