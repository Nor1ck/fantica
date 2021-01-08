pragma solidity 0.7.4;

// SPDX-License-Identifier: MIT

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
}

contract FNTLocker {
    address private FNT = 0x3d23f2E86a9AB43561203B143C18aD9De0b5C745;
    mapping (address => mapping (address => uint256)) private lockUntilTimestamp;

    function secondsLeft(address owner) external view returns (uint256) {
        require(lockUntilTimestamp[msg.sender][FNT] > 0, "Lock timestamp is not set.");
        if (block.timestamp < lockUntilTimestamp[owner][FNT]) {
            return lockUntilTimestamp[owner][FNT] - block.timestamp;
        } else {
            return 0;
        }
    }

    function blockTimestamp() external view returns (uint256) {
        return block.timestamp;
    }

    function lock(uint256 timestamp) external {
        require(lockUntilTimestamp[msg.sender][FNT] == 0, "Lock timestamp is already set.");
        IERC20 erc20 = IERC20(FNT);
        require(erc20.balanceOf(address(this)) > 0, "Send FNT to this contract first.");
        require(timestamp >= block.timestamp + 1 minutes, "Minimum 1 minute.");
        require(timestamp <= block.timestamp + 365 days, "Maximum 1 year.");
        lockUntilTimestamp[msg.sender][FNT] = timestamp;
    }

    function restore() external {
        IERC20 erc20 = IERC20(FNT);
        require(erc20.balanceOf(address(this)) > 0, "FNT not found.");
        require(lockUntilTimestamp[msg.sender][FNT] > 0, "Lock timestamp is not set.");
        require(block.timestamp >= lockUntilTimestamp[msg.sender][FNT], "FNT still locked.");
        assert(erc20.transfer(msg.sender, erc20.balanceOf(address(this))));
        lockUntilTimestamp[msg.sender][FNT] = 0;
    }
}