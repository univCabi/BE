// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract CabinetHistoryNFT is ERC721URIStorage, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;
    
    // 캐비넷 사용 기록 구조체
    struct CabinetUsage {
        uint256 cabinetId;
        uint256 historyId;  // Django의 cabinet_histories.id 저장
        address user;
        uint256 startTime;
        uint256 expiredAt;
        uint256 endedAt;    // 0이면 아직 사용 중
        string status;      // "ASSIGNED", "RETURNED" 등
    }
    
    // 토큰 ID로 캐비넷 사용 기록 매핑
    mapping(uint256 => CabinetUsage) public cabinetUsages;
    
    // Django 히스토리 ID로 토큰 ID 매핑
    mapping(uint256 => uint256) public historyIdToTokenId;
    
    // 이벤트 정의
    event CabinetAssigned(
        uint256 tokenId, 
        uint256 cabinetId, 
        uint256 historyId,
        address user, 
        uint256 startTime,
        uint256 expiredAt
    );
    
    event CabinetReturned(
        uint256 tokenId, 
        uint256 cabinetId, 
        uint256 historyId,
        address user, 
        uint256 endedAt
    );
    
    constructor() ERC721("CabinetHistoryNFT", "CABINET") {}
    
    // 캐비넷 할당 (NFT 발행)
    function assignCabinet(
        uint256 cabinetId,
        uint256 historyId,
        address user,
        uint256 startTime,
        uint256 expiredAt
    ) public onlyOwner returns (uint256) {
        // 이미 등록된 히스토리 ID인지 확인
        require(historyIdToTokenId[historyId] == 0, "History already recorded");
        
        // 새 토큰 ID 생성
        _tokenIds.increment();
        uint256 newTokenId = _tokenIds.current();
        
        // NFT 발행
        _mint(user, newTokenId);
        
        // 캐비넷 사용 기록 저장
        cabinetUsages[newTokenId] = CabinetUsage({
            cabinetId: cabinetId,
            historyId: historyId,
            user: user,
            startTime: startTime,
            expiredAt: expiredAt,
            endedAt: 0,
            status: "ASSIGNED"
        });
        
        // 히스토리 ID에 토큰 ID 매핑
        historyIdToTokenId[historyId] = newTokenId;
        
        // 이벤트 발생
        emit CabinetAssigned(
            newTokenId, 
            cabinetId, 
            historyId,
            user, 
            startTime,
            expiredAt
        );
        
        return newTokenId;
    }
    
    // 캐비넷 반납
    function returnCabinet(uint256 historyId, uint256 endedAt) public onlyOwner {
        uint256 tokenId = historyIdToTokenId[historyId];
        require(tokenId != 0, "History not found");
        
        CabinetUsage storage usage = cabinetUsages[tokenId];
        require(usage.endedAt == 0, "Cabinet already returned");
        
        // 반납 처리
        usage.endedAt = endedAt;
        usage.status = "RETURNED";
        
        // 이벤트 발생
        emit CabinetReturned(
            tokenId, 
            usage.cabinetId, 
            historyId,
            usage.user, 
            endedAt
        );
    }
    
    // 토큰 ID로 캐비넷 사용 기록 조회
    function getCabinetUsageByTokenId(uint256 tokenId) public view returns (
        uint256 cabinetId,
        uint256 historyId,
        address user,
        uint256 startTime,
        uint256 expiredAt,
        uint256 endedAt,
        string memory status
    ) {
        CabinetUsage memory usage = cabinetUsages[tokenId];
        return (
            usage.cabinetId,
            usage.historyId,
            usage.user,
            usage.startTime,
            usage.expiredAt,
            usage.endedAt,
            usage.status
        );
    }
    
    // 히스토리 ID로 캐비넷 사용 기록 조회
    function getCabinetUsageByHistoryId(uint256 historyId) public view returns (
        uint256 tokenId,
        uint256 cabinetId,
        address user,
        uint256 startTime,
        uint256 expiredAt,
        uint256 endedAt,
        string memory status
    ) {
        uint256 tokenId = historyIdToTokenId[historyId];
        require(tokenId != 0, "History not found");
        
        CabinetUsage memory usage = cabinetUsages[tokenId];
        return (
            tokenId,
            usage.cabinetId,
            usage.user,
            usage.startTime,
            usage.expiredAt,
            usage.endedAt,
            usage.status
        );
    }
    
    // 메타데이터 URI 설정
    function setTokenURI(uint256 tokenId, string memory tokenURI) public onlyOwner {
        _setTokenURI(tokenId, tokenURI);
    }
}