"use client";

import React, { useEffect, useState } from 'react';
import { Button, Input, Modal, Switch, notification, Card, Typography, Spin } from 'antd';
import styles from './Home.module.css';
import Head from 'next/head';

const { Title, Text } = Typography;

// パラメータの設定
const coilStart = 200;
const coilCount = 13;
const indicatorStart = 1100;
const indicatorCount = 10;
const registerStart = 0;
const registerCount = 4;
const discreteInputStart = 0;
const discreteInputCount = 0;
const inputRegisterStart = 0;
const inputRegisterCount = 0;
const pageTitle = 'Modbus TCP Control Panel';
const ip = '192.168.1.53';

const Home = () => {
    const [coils, setCoils] = useState<boolean[]>(Array(coilCount).fill(false));
    const [indicators, setIndicators] = useState<boolean[]>(Array(indicatorCount).fill(false));
    const [registers, setRegisters] = useState<number[]>(Array(registerCount).fill(0));
    const [discreteInputs, setDiscreteInputs] = useState<boolean[]>(Array(discreteInputCount).fill(false));
    const [inputRegisters, setInputRegisters] = useState<number[]>(Array(inputRegisterCount).fill(0));
    const [modalVisible, setModalVisible] = useState(false);
    const [selectedRegister, setSelectedRegister] = useState<number | null>(null);
    const [inputValue, setInputValue] = useState<number>(0);
    const [loading, setLoading] = useState<boolean[]>(Array(coilCount).fill(false));
    const [allStopLoading, setAllStopLoading] = useState<boolean>(false);
    const [emergencyStopLoading, setEmergencyStopLoading] = useState<boolean>(false);

    useEffect(() => {
        const fetchModbusData = async () => {
            try {
                const response = await fetch(`http://${ip}:8000/modbus/readAll?discrete_start=${discreteInputStart}&discrete_count=${discreteInputCount}&input_start=${inputRegisterStart}&input_count=${inputRegisterCount}&coil_start=${coilStart}&coil_count=${coilCount}&holding_start=${registerStart}&holding_count=${registerCount}&indicator_start=${indicatorStart}&indicator_count=${indicatorCount}`);
                if (!response.ok) {
                    throw new Error(`Error: ${response.status}`);
                }
                const data = await response.json();
                setCoils(data.coils.slice(0, coilCount)); // 必要な長さだけを設定
                setIndicators(data.indicators.slice(0, indicatorCount)); // 必要な長さだけを設定
                setRegisters(data.holding_registers.slice(0, registerCount)); // 必要な長さだけを設定
                setDiscreteInputs(data.discrete_inputs.slice(0, discreteInputCount)); // 必要な長さだけを設定
                setInputRegisters(data.input_registers.slice(0, inputRegisterCount)); // 必要な長さだけを設定
                console.log(data);
            } catch (error) {
                console.error("Failed to fetch Modbus data:", error);
            }
        };

        fetchModbusData();

        const interval = setInterval(fetchModbusData, 3000);

        return () => clearInterval(interval);
    }, []);

    const handleToggle = async (index: number) => {
        if (loading[index]) return;
        setLoading(prev => {
            const newLoading = [...prev];
            newLoading[index] = true;
            return newLoading;
        });

        const newState = !coils[index];
        try {
            const response = await fetch(`http://${ip}:8000/modbus/writeCoil`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ address: coilStart + index, value: newState }),
            });

            if (!response.ok) {
                throw new Error(`Error: ${response.status}`);
            }
            const result = await response.json();
            if (result.success) {
                setCoils(prev => {
                    const newCoils = [...prev];
                    newCoils[index] = newState;
                    return newCoils;
                });
                notification.success({ message: `Coil ${coilStart + index} updated successfully!` });
            }
        } catch (error) {
            console.error("Failed to toggle coil:", error);
            notification.error({ message: `Failed to update Coil ${coilStart + index}.` });
        } finally {
            setTimeout(() => {
                setLoading(prev => {
                    const newLoading = [...prev];
                    newLoading[index] = false;
                    return newLoading;
                });
            }, 1000);
        }
    };

    const handleRegisterClick = (index: number) => {
        setSelectedRegister(index);
        setInputValue(registers[index]);
        setModalVisible(true);
    };

    const handleModalOk = async () => {
        if (selectedRegister !== null) {
            try {
                const response = await fetch(`http://${ip}:8000/modbus/writeHoldingRegister`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ address: registerStart + selectedRegister, value: inputValue }),
                });
                if (!response.ok) {
                    throw new Error(`Error: ${response.status}`);
                }
                const result = await response.json();
                if (result.success) {
                    setRegisters(prev => {
                        const newRegisters = [...prev];
                        newRegisters[selectedRegister] = inputValue;
                        return newRegisters;
                    });
                    notification.success({ message: `Register ${registerStart + selectedRegister} updated successfully!` });
                }
            } catch (error) {
                console.error("Failed to update register:", error);
                notification.error({ message: `Failed to update Register ${registerStart + selectedRegister}.` });
            } finally {
                setModalVisible(false);
            }
        }
    };

    const handleStopAll = async () => {
        setAllStopLoading(true);
        try {
            // holding resister 130, 131, 133, 135, 137をOFFにする
            const response = await fetch(`http://${ip}:8000/modbus/writeCoil`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ address: 206, value: 1 }),
            });
        }
        catch (error) {
            console.error("Failed to stop all mission works:", error);
            notification.error({ message: 'Failed to stop all mission works.' });
        } finally {
            setAllStopLoading(false);
        }
        try {
            const response = await fetch(`http://${ip}:8000/missionWorks/stopAll`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
            if (!response.ok) {
                throw new Error(`Error: ${response.status}`);
            }
            const result = await response.json();
            if (result.success) {
                notification.success({ message: 'All mission works stopped successfully!' });
            }
        } catch (error) {
            console.error("Failed to stop all mission works:", error);
            notification.error({ message: 'Failed to stop all mission works.' });
        } finally {
            setAllStopLoading(false);
        }
    };

    const handleEmergencyStop = async () => {
        setEmergencyStopLoading(true);
        try {
            const response = await fetch(`http://${ip}:8000/vehicles/emergencyStop`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
            if (!response.ok) {
                throw new Error(`Error: ${response.status}`);
            }
            const result = await response.json();
            if (result.success) {
                notification.success({ message: 'Emergency stop executed successfully!' });
            }
        } catch (error) {
            console.error("Failed to execute emergency stop:", error);
            notification.error({ message: 'Failed to execute emergency stop.' });
        } finally {
            setEmergencyStopLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <Head>
                <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Permanent+Marker&display=swap" />
            </Head>
            <div className={styles.fixedHeader}>
                <Title level={2} className={styles.title}>{pageTitle}</Title>
                <Button
                    type="primary"
                    onClick={handleStopAll}
                    loading={allStopLoading}
                    className={styles.stopAllButton}
                >
                    STOP ALL
                </Button>
            </div>
            <div className={styles.content}>
                {Array.from({ length: coilCount }).map((_, index) => (
                    <Card
                        key={index}
                        title={`Coil ${coilStart + index}`}
                        bordered={false}
                        className={`${styles.card} ${indicators[index] ? styles.on : ''}`}
                    >
                        <Text className={styles.text}>
                            {
                                // index === 0 ? 'DEMO 1' :
                                // index === 1 ? 'HOME' :
                                // index === 2 ? 'Docomo Area' :
                                // index === 3 ? 'Entrance' :
                                // index === 4 ? 'Center' :
                                // index === 5 ? 'Backroom' :
                                // index === 10 ? 'juuden' : ''
                                index === 0 ? 'テーブル取得' :
                                index === 1 ? 'テーブル返却' :
                                index === 2 ? 'ポイント０へ移動' :
                                index === 3 ? 'ポイント１へ移動' :
                                index === 4 ? 'ポイント２へ移動' :
                                index === 5 ? '連続ON' :
                                index === 6 ? '停止' :
                                index === 7 ? 'テーブル１or２' :
                                index === 8 ? 'ユニパルスへ移動' : 
                                index === 9 ? 'ダッシュ' :  
                                index === 10 ? 'めんたいこ味' :  
                                index === 11 ? 'チーズ味' :  
                                index === 12 ? 'コンポタ味' : ''
                            }
                        </Text>
                        <Switch
                            checked={coils[index]}
                            onChange={() => handleToggle(index)}
                            loading={loading[index]}
                            checkedChildren="ON"
                            unCheckedChildren="OFF"
                            className={styles.switch}
                        />
                    </Card>
                ))}
                {Array.from({ length: discreteInputCount }).map((_, index) => (
                    <Card
                        key={index}
                        title={`Discrete Input ${discreteInputStart + index}`}
                        bordered={false}
                        className={styles.card}
                    >
                        <Text className={styles.text}>
                            {discreteInputs[index] ? 'ON' : 'OFF'}
                        </Text>
                    </Card>
                ))}
                {Array.from({ length: inputRegisterCount }).map((_, index) => (
                    <Card
                        key={index}
                        title={`Input Register ${inputRegisterStart + index}`}
                        bordered={false}
                        className={styles.card}
                    >
                        <Text className={styles.registerText}>{inputRegisters[index]}</Text>
                    </Card>
                ))}
                {Array.from({ length: registerCount }).map((_, index) => (
                    <Card
                        key={index}
                        title={`Holding Register ${registerStart + index}`}
                        bordered={false}
                        className={styles.card}
                        onClick={() => handleRegisterClick(index)}
                    >
                        
                        <Text className={styles.text}>
                            {
                                index === 0 ? 'ポイント０' :
                                index === 1 ? 'ポイント１' :
                                index === 2 ? 'ポイント２' :
                                index === 3 ? 'マップ番号' : ''
                            }
                        </Text>
                        <Text className={styles.registerText}>{registers[index]}</Text>
                    </Card>
                    
                ))}
            </div>
            <Modal
                title={`Update Register ${selectedRegister !== null ? registerStart + selectedRegister : ''}`}
                open={modalVisible}
                onOk={handleModalOk}
                onCancel={() => setModalVisible(false)}
                className={styles.modal}
            >
                <Input
                    type="number"
                    value={inputValue}
                    onChange={(e) => setInputValue(Number(e.target.value))}
                    className={styles.input}
                />
            </Modal>
        </div>
    );
};

export default Home;
