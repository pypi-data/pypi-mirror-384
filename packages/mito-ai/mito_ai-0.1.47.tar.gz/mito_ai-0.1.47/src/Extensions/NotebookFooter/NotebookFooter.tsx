/*
 * Copyright (c) Saga Inc.
 * Distributed under the terms of the GNU Affero General Public License v3.0 License.
 */

import React, { useEffect } from "react";
import { useState } from "react";
import { INotebookTracker, NotebookActions } from "@jupyterlab/notebook";
import { JupyterFrontEnd } from "@jupyterlab/application";
import { COMMAND_MITO_AI_SEND_AGENT_MESSAGE, COMMAND_MITO_AI_OPEN_CHAT } from "../../commands";
import '../../../style/NotebookFooter.css';
import LoadingCircle from "../../components/LoadingCircle";
import CodeIcon from "../../icons/NotebookFooter/CodeIcon";
import TextIcon from "../../icons/NotebookFooter/TextIcon";
import { userSignupEvents } from '../../utils/userSignupEvents';
import { checkUserSignupState } from '../../utils/userSignupState';

interface NotebookFooterProps {
    notebookTracker: INotebookTracker;
    app: JupyterFrontEnd;
}

const NotebookFooter: React.FC<NotebookFooterProps> = ({ notebookTracker, app }) => {
    const notebook = notebookTracker.currentWidget?.content

    const [inputValue, setInputValue] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [isSignedUp, setIsSignedUp] = useState(true);

    // Function to refresh user signup state using the shared helper
    const refreshUserSignupState = async (): Promise<void> => {
        const signupState = await checkUserSignupState();
        setIsSignedUp(signupState.isSignedUp);
    };

    useEffect(() => {
        void refreshUserSignupState();
    }, []);

    // Listen for signup success events from other components
    useEffect(() => {
        const handleSignupSuccess = (): void => {
            void refreshUserSignupState();
        };

        userSignupEvents.signupSuccess.connect(handleSignupSuccess);

        // Cleanup the event listener when component unmounts
        return () => {
            userSignupEvents.signupSuccess.disconnect(handleSignupSuccess);
        };
    }, []);

    // If the notebook is not loaded yet, don't render anything
    if (notebook === undefined || notebook.model === null) {
        return null;
    }

    const getPlaceholder = (): string => {
        if (isGenerating) {
            return 'Generating notebook...';
        } else if (isSignedUp) {
            return 'What analysis can I help you with?';
        } else {
            return 'Sign up to use Mito AI (see taskpane on the left)';
        }
    };

    const addCell = (cellType: 'code' | 'markdown' = 'code'): void => {
        if (notebook.widgets.length && notebook.widgets.length > 0) {
            notebook.activeCellIndex = notebook.widgets.length - 1;
        }

        if (cellType === 'code') {
            NotebookActions.insertBelow(notebook);
        } else {
            NotebookActions.insertBelow(notebook);
            // Change the cell type after insertion
            const activeCell = notebook.activeCell;
            if (activeCell && activeCell.model.type !== cellType) {
                NotebookActions.changeCellType(notebook, cellType);
            }
        }

        void NotebookActions.focusActiveCell(notebook);
    };

    const handleInputSubmit = (): void => {
        const _handleInputSubmitAsync = async (): Promise<void> => {
            const submittedInput = inputValue.trim();
            if (submittedInput !== '') {
                setIsGenerating(true);
                setInputValue('');
                await app.commands.execute(COMMAND_MITO_AI_OPEN_CHAT, { focusChatInput: false });
                await app.commands.execute(COMMAND_MITO_AI_SEND_AGENT_MESSAGE, { input: submittedInput });
                setIsGenerating(false);
            }
        }

        void _handleInputSubmitAsync();
    };

    /* 
    We handle keypress events to prevent JupyterLab from intercepting keyboard events
    and taking some other action while the user is typing in this input field. Jupyter 
    might otherwise do things like: change cell type, move focus to a cell, etc. 
    */
    const handleKeyPress = (e: React.KeyboardEvent): void => {
        e.stopPropagation();
    };
    const handleInputFocus = (e: React.FocusEvent<HTMLInputElement>): void => {
        e.stopPropagation();
    };
    const handleInputBlur = (e: React.FocusEvent<HTMLInputElement>): void => {
        e.stopPropagation();
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
        e.stopPropagation();
        setInputValue(e.target.value);
    };

    const handleKeyDown = (e: React.KeyboardEvent): void => {
        e.stopPropagation();

        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleInputSubmit();
        }
    };

    return (
        <div className="notebook-footer-container">
            {/* Input field */}
            <div className="input-container">
                <div className={`input-wrapper ${isGenerating ? 'generating' : ''}`}>
                    <div className="input-icon-left">
                        {isGenerating ? (
                            <LoadingCircle />
                        ) : (
                            <>✦</>
                        )}
                    </div>
                    <input
                        type="text"
                        value={inputValue}
                        onChange={handleInputChange}
                        onKeyDown={handleKeyDown}
                        onKeyPress={handleKeyPress}
                        onFocus={handleInputFocus}
                        onBlur={handleInputBlur}
                        placeholder={getPlaceholder()}
                        className="prompt-input"
                        autoComplete="off"
                        spellCheck={false}
                        disabled={isGenerating || !isSignedUp}
                    />
                    <div className="input-icons-right">
                        <button
                            className="input-action-button"
                            onClick={handleInputSubmit}
                            onMouseDown={(e) => e.stopPropagation()}
                        >
                            ▶
                        </button>
                    </div>
                </div>
            </div>

            {/* Button row */}
            <div className="button-row">
                {/* Python button */}
                <button
                    onClick={() => addCell('code')}
                    className="footer-button"
                    onMouseDown={(e) => e.stopPropagation()}
                >
                    <div className="button-content">
                        <div className="button-icon">
                            <CodeIcon />
                        </div>
                        <span className="button-label">Python</span>
                    </div>
                </button>

                {/* Text button */}
                <button
                    onClick={() => addCell('markdown')}
                    className="footer-button"
                    onMouseDown={(e) => e.stopPropagation()}
                >
                    <div className="button-content">
                        <div className="button-icon">
                            <TextIcon />
                        </div>
                        <span className="button-label">Text</span>
                    </div>
                </button>
            </div>
        </div>
    );
};

export default NotebookFooter;