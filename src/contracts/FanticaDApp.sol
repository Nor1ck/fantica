pragma solidity 0.7.0;

// SPDX-License-Identifier: MIT

interface IERC20 {
    function transfer(address recipient, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
}

abstract contract MsgContext {
    function _msgSender() internal view virtual returns (address payable) {
        return msg.sender;
    }
}

library SafeMath {
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a, "SafeMath: addition overflow");

        return c;
    }

    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        return sub(a, b, "SafeMath: subtraction overflow");
    }

    function sub(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
        require(b <= a, errorMessage);
        uint256 c = a - b;

        return c;
    }

    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        if (a == 0) {
            return 0;
        }

        uint256 c = a * b;
        require(c / a == b, "SafeMath: multiplication overflow");

        return c;
    }

    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        return div(a, b, "SafeMath: division by zero");
    }

    function div(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
        require(b > 0, errorMessage);
        uint256 c = a / b;
        return c;
    }
}

abstract contract Ownable is MsgContext {
    address private _owner;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    constructor () {
        address msgSender = _msgSender();
        _owner = msgSender;
        emit OwnershipTransferred(address(0), msgSender);
    }

    function owner() public view returns (address) {
        return _owner;
    }

    modifier onlyOwner() {
        require(_owner == _msgSender(), "Ownable: caller is not the owner");
        _;
    }

    // If you transfer ownership to a contract address, make sure that it knows how to handle DAI funds and implements IERC20
    function transferOwnership(address newOwner) public virtual onlyOwner {
        require(newOwner != address(0), "Ownable: new owner is the zero address");
        emit OwnershipTransferred(_owner, newOwner);
        _owner = newOwner;
    }
}

contract FanticaDApp is Ownable {
    using SafeMath for uint256;
    enum SubscriptionPeriod { None, Monthly, Annual }

    address private DAI = 0x6B175474E89094C44Da98b954EedeAC495271d0F;
    uint256 private DEFAULT_CONTENT_PRICE =  1 ether; //   1 DAI (ether stands for 18 decimals)
    uint256 private DEFAULT_MONTHLY_PRICE =  10 ether; //  10 DAI
    uint256 private DEFAULT_ANNUAL_PRICE = 100 ether; // 100 DAI

    mapping (address => uint256) private _daiBalances;
    mapping (address => bool) private _subscriptionAccessIsFree;
    mapping (address => mapping (address => SubscriptionPeriod)) private _subscriptionPeriod;
    mapping (address => mapping (address => uint256)) private _subscriptionExpires;
    mapping (address => mapping (SubscriptionPeriod => uint256)) private _subscriptionPrice;

    // Used for renewal of subscription if the price has not changed or has become lower, the subscription will be renewed.
    mapping (address => mapping (address => uint256)) private _subscriberRenewalPrice;
    // A price per content unit for a specific creator.
    mapping (address => uint256) private _contentPrice;
    mapping (address => mapping(address => mapping(uint256 => bool))) private _purchases;

    event Purchase(address indexed creator, uint256 indexed contentId, uint256 price);
    event Tips(address indexed creator, uint256 indexed contentId, uint256 amount);
    event Subscribe(address indexed consumer, address indexed creator, uint256 price, uint256 expires);
    event SubscriptionRenewal(address indexed consumer, address indexed creator, uint256 price, uint256 expires);
    event SubscriptionCancel(address indexed consumer, address indexed creator);
    event SubscriptionChanged(address indexed consumer, address indexed creator, SubscriptionPeriod oldPeriod, SubscriptionPeriod newPeriod);
    event Withdrawal(address indexed creator, uint256 amount);

    // ===========================================================
	// Getter & Setter
	// ===========================================================

    function canView(address consumer, address creator) external view returns (bool) {
        if (consumer == creator) return true;
        if (IERC20(DAI).allowance(consumer, address(this)) >= DEFAULT_CONTENT_PRICE) {
            return block.timestamp <= _subscriptionExpires[consumer][creator] || _subscriptionAccessIsFree[creator] ? true : false;
        }
        return false;
    }

    function balanceOfDAI(address who) external view returns (uint256) {
        return _daiBalances[who];
    }

    function subscriptionAccessIsFree(address creator) external view returns (bool) {
        return _subscriptionAccessIsFree[creator];
    }

    function subscriptionPeriod(address consumer, address creator) external view returns (SubscriptionPeriod) {
        return _subscriptionPeriod[consumer][creator];
    }

    function getExpiration(SubscriptionPeriod period) private view returns (uint256) {
        return period == SubscriptionPeriod.Annual ? block.timestamp + 365 days : block.timestamp + 30 days;
    }

    function subscriptionPrice(address creator, SubscriptionPeriod period) public view returns (uint256) {
        require(period != SubscriptionPeriod.None, "Please select Monthly or Annual.");
        uint256 price = _subscriptionPrice[creator][period];
        if (period == SubscriptionPeriod.Annual) {
            return _subscriptionAccessIsFree[creator] ? 0 : price > 0 ? price : DEFAULT_ANNUAL_PRICE;
        }
        return _subscriptionAccessIsFree[creator] ? 0 : price > 0 ? price : DEFAULT_MONTHLY_PRICE;
    }

    function contentPrice(address creator) public view returns (uint256) {
        return _subscriptionAccessIsFree[creator] ? 0 : _contentPrice[creator] > 0 ? _contentPrice[creator] : DEFAULT_CONTENT_PRICE;
    }

    function contentPurchased(address consumer, address creator, uint256 contentId) external view returns (bool) {
        return _purchases[consumer][creator][contentId];
    }

    function setSubscriptionPrice(uint256 monthlyPrice, uint256 annualPrice) external {
        _subscriptionPrice[_msgSender()][SubscriptionPeriod.Monthly] = monthlyPrice;
        _subscriptionPrice[_msgSender()][SubscriptionPeriod.Annual] = annualPrice;
    }

    function setSubscriptionAccess(bool isFree) external {
        require(_subscriptionAccessIsFree[_msgSender()] != isFree, "The value is already set.");
        _subscriptionAccessIsFree[_msgSender()] = isFree;
    }

    function setContentPrice(uint256 price) external {
        require(_contentPrice[_msgSender()] != price, "The value is already set.");
        _contentPrice[_msgSender()] = price;
    }

    // ===========================================================
	// Payable
	// ===========================================================

    function sendTips(address creator, uint256 contentId, uint256 amount) external {
        require(creator != _msgSender(), "You can't send yourself tips.");
        require(amount > 0, "The amount is zero.");

        require(IERC20(DAI).allowance(_msgSender(), address(this)) >= amount, "DAI insufficient allowance.");

        IERC20(DAI).transferFrom(_msgSender(), address(this), amount);

        // Charging fees, updating DAI balances
        uint256 fee = amount.mul(5).div(100);
        _daiBalances[address(this)] = _daiBalances[address(this)].add(fee);
        _daiBalances[creator] = _daiBalances[creator].add(amount).sub(fee);

        emit Tips(creator, contentId, amount);
    }

    function purchase(address creator, uint256 contentId) external {
        require(creator != _msgSender(), "You can't buy from yourself.");
        require(!_purchases[_msgSender()][creator][contentId], "The content is already purchased.");
        uint256 price = contentPrice(creator);
        require(price > 0, "The content is free.");

        require(IERC20(DAI).allowance(_msgSender(), address(this)) >= price, "DAI insufficient allowance.");

        IERC20(DAI).transferFrom(_msgSender(), address(this), price);

        // Charging fees, updating DAI balances
        uint256 fee = price.mul(5).div(100);
        _daiBalances[address(this)] = _daiBalances[address(this)].add(fee);
        _daiBalances[creator] = _daiBalances[creator].add(price).sub(fee);

        emit Purchase(creator, contentId, price);
        _purchases[_msgSender()][creator][contentId] = true;
    }

    function subscribe(address creator, SubscriptionPeriod period) external {
        require(creator != _msgSender(), "You can't subscribe to yourself.");
        require(_subscriptionPeriod[_msgSender()][creator] == SubscriptionPeriod.None, "Your subscription is already active.");
        require(_subscriptionExpires[_msgSender()][creator] <= block.timestamp, "Your subscription hasn't expired yet.");
        require(!_subscriptionAccessIsFree[creator], "Subscription is not required.");
        // TODO if the price has become higher, re-subscribe
        uint256 price = subscriptionPrice(creator, period);
        IERC20(DAI).transferFrom(_msgSender(), address(this), price);

        // Charging fees, updating DAI balances
        uint256 fee = price.mul(5).div(100);
        _daiBalances[address(this)] = _daiBalances[address(this)].add(fee);
        _daiBalances[creator] = _daiBalances[creator].add(price).sub(fee);

        uint256 expires = getExpiration(period);
        _subscriptionExpires[_msgSender()][creator] = expires;
        _subscriberRenewalPrice[_msgSender()][creator] = price;
        _subscriptionPeriod[_msgSender()][creator] = period;
        emit Subscribe(_msgSender(), creator, price, expires);
    }

    function renewSubscription(address consumer, address creator) external {
        require(_subscriptionExpires[consumer][creator] != 0, "Subscription not found.");
        require(_subscriptionExpires[consumer][creator] <= block.timestamp, "Subscription hasn't expired yet.");
        require(!_subscriptionAccessIsFree[creator], "No renewal is required for a free subscription.");

        SubscriptionPeriod currenPeriod = _subscriptionPeriod[consumer][creator];
        require(currenPeriod != SubscriptionPeriod.None, "Subscription was canceled.");

        uint256 price = subscriptionPrice(creator, currenPeriod);
        require(_subscriberRenewalPrice[consumer][creator] >= price, "The subscription price has increased confirmation is required.");

        IERC20(DAI).transferFrom(consumer, address(this), price);

        // Charging fees, updating DAI balances
        uint256 fee = price.mul(5).div(100);
        _daiBalances[address(this)] = _daiBalances[address(this)].add(fee);
        _daiBalances[creator] = _daiBalances[creator].add(price).sub(fee);

        uint256 expires = getExpiration(currenPeriod);
        _subscriptionExpires[consumer][creator] = expires;
        emit SubscriptionRenewal(consumer, creator, price, expires);
    }

    // ===========================================================
	// Subscription control
	// ===========================================================

    function cancelSubscription(address creator) external {
        require(_subscriptionPeriod[_msgSender()][creator] != SubscriptionPeriod.None, "Subscription not found.");
        _subscriptionPeriod[_msgSender()][creator] = SubscriptionPeriod.None;
        emit SubscriptionCancel(_msgSender(), creator);
    }

    // Used if the subscription price has increased.
    function confirmNewSubscriptionPrice(address creator) external {
        SubscriptionPeriod currenPeriod = _subscriptionPeriod[_msgSender()][creator];
        require(currenPeriod != SubscriptionPeriod.None, "Subscription not found.");
        _subscriberRenewalPrice[_msgSender()][creator] = _subscriptionPrice[creator][currenPeriod];
    }

    function switchSubscriptionToMonthly(address creator) external {
        require(!_subscriptionAccessIsFree[creator], "No Monthly is required for a free subscription.");
        require(_subscriptionPeriod[_msgSender()][creator] == SubscriptionPeriod.Annual, "Annual subscription not found.");
        _subscriberRenewalPrice[_msgSender()][creator] = _subscriptionPrice[creator][SubscriptionPeriod.Monthly];
        emit SubscriptionChanged(_msgSender(), creator, _subscriptionPeriod[_msgSender()][creator], SubscriptionPeriod.Monthly);
        _subscriptionPeriod[_msgSender()][creator] = SubscriptionPeriod.Monthly;
        _subscriberRenewalPrice[_msgSender()][creator] = subscriptionPrice(creator, SubscriptionPeriod.Monthly);
    }

    function switchSubscriptionToAnnual(address creator) external {
        require(!_subscriptionAccessIsFree[creator], "No Annual is required for a free subscription.");
        require(_subscriptionPeriod[_msgSender()][creator] == SubscriptionPeriod.Monthly, "Monthly subscription not found.");
        _subscriberRenewalPrice[_msgSender()][creator] = _subscriptionPrice[creator][SubscriptionPeriod.Annual];
        emit SubscriptionChanged(_msgSender(), creator, _subscriptionPeriod[_msgSender()][creator], SubscriptionPeriod.Annual);
        _subscriptionPeriod[_msgSender()][creator] = SubscriptionPeriod.Annual;
        _subscriberRenewalPrice[_msgSender()][creator] = subscriptionPrice(creator, SubscriptionPeriod.Annual);
    }

    // ===========================================================
	// Withdraw DAI balances
	// ===========================================================

    function withdrawDAI() external {
        uint256 balance = _daiBalances[_msgSender()];
        require(balance > 0, "Your balance is zero.");
        _daiBalances[_msgSender()] = _daiBalances[_msgSender()].sub(balance);
        IERC20(DAI).transfer(_msgSender(), balance);
        emit Withdrawal(_msgSender(), balance);
    }

    function withdrawDAIFees() external onlyOwner {
        uint256 balance = _daiBalances[address(this)];
        require(balance > 0, "Your balance is zero.");
        _daiBalances[address(this)] = _daiBalances[address(this)].sub(balance);
        IERC20(DAI).transfer(_msgSender(), balance);
        emit Withdrawal(_msgSender(), balance);
    }
}