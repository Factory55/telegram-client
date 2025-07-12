import os
import logging
import threading
import time
from typing import Set, Optional
from config import Config

class ChatFilter:
    def __init__(self, allowed_chats_file: str = "allowed_chats.txt"):
        self.logger = logging.getLogger(__name__)
        self.allowed_chats_file = allowed_chats_file
        self.allowed_chat_names: Set[str] = set()
        self.last_modified_time = 0
        self.lock = threading.Lock()
        
        # Load initial allowed chats
        self._load_allowed_chats()
        
        # Start monitoring thread for file changes
        self.monitoring_thread = threading.Thread(
            target=self._monitor_file_changes,
            daemon=True
        )
        self.monitoring_thread.start()
        
        self.logger.info(f"Chat filter initialized with {len(self.allowed_chat_names)} allowed chats")
    
    def _load_allowed_chats(self) -> None:
        """Load allowed chat names from file"""
        try:
            if not os.path.exists(self.allowed_chats_file):
                self.logger.warning(f"Allowed chats file '{self.allowed_chats_file}' not found. Creating empty file.")
                self._create_empty_file()
                return
            
            # Check if file has been modified
            current_modified_time = os.path.getmtime(self.allowed_chats_file)
            if current_modified_time <= self.last_modified_time:
                return  # No changes
            
            with open(self.allowed_chats_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Parse chat names (strip whitespace and ignore empty lines)
            new_allowed_chats = set()
            for line in lines:
                chat_name = line.strip()
                if chat_name and not chat_name.startswith('#'):  # Ignore comments
                    new_allowed_chats.add(chat_name)
            
            with self.lock:
                old_count = len(self.allowed_chat_names)
                self.allowed_chat_names = new_allowed_chats
                self.last_modified_time = current_modified_time
            
            self.logger.info(f"Loaded {len(new_allowed_chats)} allowed chats (was {old_count})")
            
            # Log the allowed chats for debugging
            if new_allowed_chats:
                self.logger.debug(f"Allowed chats: {', '.join(sorted(new_allowed_chats))}")
            else:
                self.logger.warning("No allowed chats found in file")
                
        except Exception as e:
            self.logger.error(f"Error loading allowed chats from '{self.allowed_chats_file}': {e}")
    
    def _create_empty_file(self) -> None:
        """Create an empty allowed chats file with example content"""
        try:
            with open(self.allowed_chats_file, 'w', encoding='utf-8') as f:
                f.write("# Add allowed chat names here (one per line)\n")
                f.write("# Lines starting with # are comments\n")
                f.write("# Example:\n")
                f.write("# The Beard Chat\n")
                f.write("# Citadel to the beard\n")
                f.write("# CFB Bets\n")
                f.write("# Test Beard Telegram Client\n")
            
            self.logger.info(f"Created empty allowed chats file: {self.allowed_chats_file}")
        except Exception as e:
            self.logger.error(f"Error creating allowed chats file: {e}")
    
    def _monitor_file_changes(self) -> None:
        """Monitor the allowed chats file for changes"""
        self.logger.info(f"Started monitoring '{self.allowed_chats_file}' for changes")
        
        while True:
            try:
                time.sleep(5)  # Check every 5 seconds
                self._load_allowed_chats()
            except Exception as e:
                self.logger.error(f"Error in file monitoring thread: {e}")
                time.sleep(10)  # Wait longer on error
    
    def is_chat_allowed(self, chat_title: Optional[str]) -> bool:
        """
        Check if a chat is allowed based on its title
        
        Args:
            chat_title: The title/name of the chat
            
        Returns:
            bool: True if chat is allowed, False otherwise
        """
        if not chat_title:
            self.logger.debug("Chat title is None or empty, denying access")
            return False
        
        with self.lock:
            is_allowed = chat_title in self.allowed_chat_names
        
        if is_allowed:
            self.logger.debug(f"Chat '{chat_title}' is allowed")
        else:
            self.logger.debug(f"Chat '{chat_title}' is not in allowed list")
        
        return is_allowed
    
    def get_allowed_chats(self) -> Set[str]:
        """Get a copy of the current allowed chat names"""
        with self.lock:
            return self.allowed_chat_names.copy()
    
    def add_allowed_chat(self, chat_name: str) -> bool:
        """
        Add a chat name to the allowed list
        
        Args:
            chat_name: The name of the chat to add
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        try:
            with open(self.allowed_chats_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{chat_name}")
            
            self.logger.info(f"Added '{chat_name}' to allowed chats")
            return True
        except Exception as e:
            self.logger.error(f"Error adding chat '{chat_name}' to allowed list: {e}")
            return False
    
    def remove_allowed_chat(self, chat_name: str) -> bool:
        """
        Remove a chat name from the allowed list
        
        Args:
            chat_name: The name of the chat to remove
            
        Returns:
            bool: True if removed successfully, False otherwise
        """
        try:
            # Read current content
            with open(self.allowed_chats_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Remove the specified chat name
            filtered_lines = []
            removed = False
            for line in lines:
                if line.strip() != chat_name:
                    filtered_lines.append(line)
                else:
                    removed = True
            
            # Write back without the removed chat
            with open(self.allowed_chats_file, 'w', encoding='utf-8') as f:
                f.writelines(filtered_lines)
            
            if removed:
                self.logger.info(f"Removed '{chat_name}' from allowed chats")
            else:
                self.logger.warning(f"Chat '{chat_name}' not found in allowed list")
            
            return removed
        except Exception as e:
            self.logger.error(f"Error removing chat '{chat_name}' from allowed list: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get statistics about the chat filter"""
        with self.lock:
            return {
                'allowed_chats_count': len(self.allowed_chat_names),
                'allowed_chats': sorted(list(self.allowed_chat_names)),
                'file_path': self.allowed_chats_file,
                'last_modified': self.last_modified_time
            } 